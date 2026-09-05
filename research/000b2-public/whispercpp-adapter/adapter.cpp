#include "ggml-backend.h"
#include "whisper.h"

#include <algorithm>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <sstream>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace {

constexpr int kSampleRate = 16000;
constexpr int kThreads = 4;
constexpr int kStepMs = 500;
constexpr int kLengthMs = 5000;
constexpr int kKeepMs = 200;
constexpr int kStepSamples = kSampleRate * kStepMs / 1000;
constexpr int kLengthSamples = kSampleRate * kLengthMs / 1000;
constexpr int kKeepSamples = kSampleRate * kKeepMs / 1000;
constexpr int kFinalZeroSamples = 10560;
constexpr int kNewLineEvery = std::max(1, kLengthMs / kStepMs - 1);

struct Args {
    std::string model;
    std::string input_list;
    std::string output;
};

struct InputRow {
    std::string utterance_id;
    std::string path;
};

struct DecodeResult {
    std::string status = "DECODED";
    std::vector<std::string> raw_lines;
    std::string raw_transcript;
    std::string failure_type;
    std::string failure_message;
    int failure_iteration = -1;
    int stream_iteration_count = 0;
    double decode_wall_seconds = 0.0;
};

[[noreturn]] void fail(const std::string & message) {
    throw std::runtime_error(message);
}

Args parse_args(int argc, char ** argv) {
    Args args;
    for (int i = 1; i < argc; ++i) {
        const std::string arg = argv[i];
        auto value = [&](const char * name) -> std::string {
            if (i + 1 >= argc) {
                fail(std::string(name) + " requires a value");
            }
            return argv[++i];
        };
        if (arg == "--model") {
            args.model = value("--model");
        } else if (arg == "--input-list") {
            args.input_list = value("--input-list");
        } else if (arg == "--output") {
            args.output = value("--output");
        } else if (arg == "--version") {
            std::cout << "wispral-whispercpp-c0-adapter-v1\n";
            std::exit(0);
        } else {
            fail("unknown argument: " + arg);
        }
    }
    if (args.model.empty() || args.input_list.empty() || args.output.empty()) {
        fail("--model, --input-list, and --output are required");
    }
    return args;
}

uint16_t le16(const unsigned char * p) {
    return static_cast<uint16_t>(p[0]) |
           (static_cast<uint16_t>(p[1]) << 8);
}

uint32_t le32(const unsigned char * p) {
    return static_cast<uint32_t>(p[0]) |
           (static_cast<uint32_t>(p[1]) << 8) |
           (static_cast<uint32_t>(p[2]) << 16) |
           (static_cast<uint32_t>(p[3]) << 24);
}

std::vector<unsigned char> read_exact(std::ifstream & input, std::size_t size, const std::string & label) {
    std::vector<unsigned char> bytes(size);
    if (size > 0) {
        input.read(reinterpret_cast<char *>(bytes.data()), static_cast<std::streamsize>(size));
        if (input.gcount() != static_cast<std::streamsize>(size)) {
            fail("truncated " + label);
        }
    }
    return bytes;
}

std::vector<float> read_pcm_s16le_mono_16k(const std::string & path) {
    std::ifstream input(path, std::ios::binary);
    if (!input.is_open()) {
        fail("unable to open WAV: " + path);
    }

    const auto header = read_exact(input, 12, "WAV header");
    if (std::string(reinterpret_cast<const char *>(header.data()), 4) != "RIFF" ||
        std::string(reinterpret_cast<const char *>(header.data() + 8), 4) != "WAVE") {
        fail("invalid RIFF/WAVE header: " + path);
    }

    bool fmt_seen = false;
    bool data_seen = false;
    uint16_t audio_format = 0;
    uint16_t channels = 0;
    uint32_t sample_rate = 0;
    uint16_t bits_per_sample = 0;
    std::vector<unsigned char> pcm_bytes;

    while (input.good() && !data_seen) {
        char id_chars[4];
        input.read(id_chars, 4);
        if (input.gcount() == 0) {
            break;
        }
        if (input.gcount() != 4) {
            fail("truncated WAV chunk id: " + path);
        }
        const auto size_bytes = read_exact(input, 4, "WAV chunk size");
        const uint32_t chunk_size = le32(size_bytes.data());
        const std::string id(id_chars, 4);

        if (id == "fmt ") {
            if (chunk_size < 16 || chunk_size > 4096) {
                fail("unexpected WAV fmt chunk size: " + path);
            }
            const auto fmt = read_exact(input, chunk_size, "WAV fmt chunk");
            audio_format = le16(fmt.data());
            channels = le16(fmt.data() + 2);
            sample_rate = le32(fmt.data() + 4);
            bits_per_sample = le16(fmt.data() + 14);
            fmt_seen = true;
        } else if (id == "data") {
            if (chunk_size == 0 || chunk_size > 64U * 1024U * 1024U) {
                fail("unexpected WAV data chunk size: " + path);
            }
            pcm_bytes = read_exact(input, chunk_size, "WAV data chunk");
            data_seen = true;
        } else {
            input.seekg(static_cast<std::streamoff>(chunk_size), std::ios::cur);
            if (!input.good()) {
                fail("unable to skip WAV chunk: " + path);
            }
        }

        if ((chunk_size & 1U) != 0U) {
            input.seekg(1, std::ios::cur);
            if (!input.good()) {
                fail("truncated WAV padding byte: " + path);
            }
        }
    }

    if (!fmt_seen || !data_seen) {
        fail("missing WAV fmt/data chunk: " + path);
    }
    if (audio_format != 1 || channels != 1 || sample_rate != kSampleRate || bits_per_sample != 16) {
        fail("WAV is not PCM_S16LE mono 16000 Hz: " + path);
    }
    if ((pcm_bytes.size() % 2U) != 0U) {
        fail("odd PCM byte count: " + path);
    }

    std::vector<float> samples;
    samples.reserve(pcm_bytes.size() / 2U + kFinalZeroSamples);
    for (std::size_t i = 0; i < pcm_bytes.size(); i += 2) {
        const uint16_t raw = le16(pcm_bytes.data() + i);
        const int16_t sample = static_cast<int16_t>(raw);
        samples.push_back(static_cast<float>(sample) / 32768.0f);
    }
    samples.insert(samples.end(), kFinalZeroSamples, 0.0f);
    return samples;
}

std::vector<InputRow> load_inputs(const std::string & path) {
    std::ifstream input(path);
    if (!input.is_open()) {
        fail("unable to open input list: " + path);
    }
    std::vector<InputRow> rows;
    std::string line;
    while (std::getline(input, line)) {
        if (line.empty()) {
            continue;
        }
        const auto tab = line.find('\t');
        if (tab == std::string::npos || tab == 0 || tab + 1 >= line.size()) {
            fail("malformed input-list row");
        }
        InputRow row{line.substr(0, tab), line.substr(tab + 1)};
        if (row.utterance_id.find('\t') != std::string::npos || row.path.find('\t') != std::string::npos) {
            fail("tab found inside input-list field");
        }
        rows.push_back(std::move(row));
    }
    if (rows.empty()) {
        fail("input list is empty");
    }
    return rows;
}

std::string json_escape(const std::string & value) {
    std::ostringstream out;
    out << '"';
    static const char hex[] = "0123456789abcdef";
    for (unsigned char ch : value) {
        switch (ch) {
            case '"': out << "\\\""; break;
            case '\\': out << "\\\\"; break;
            case '\b': out << "\\b"; break;
            case '\f': out << "\\f"; break;
            case '\n': out << "\\n"; break;
            case '\r': out << "\\r"; break;
            case '\t': out << "\\t"; break;
            default:
                if (ch < 0x20U) {
                    out << "\\u00" << hex[(ch >> 4) & 0x0f] << hex[ch & 0x0f];
                } else {
                    out << static_cast<char>(ch);
                }
        }
    }
    out << '"';
    return out.str();
}

std::string reconstruct_stream_text(const std::vector<std::string> & iterations) {
    std::string result;
    for (std::size_t i = 0; i < iterations.size(); ++i) {
        result += iterations[i];
        if (((i + 1) % static_cast<std::size_t>(kNewLineEvery)) == 0U) {
            result.push_back('\n');
        }
    }
    return result;
}

DecodeResult decode_one(whisper_context * ctx, const InputRow & input_row) {
    DecodeResult result;
    const auto started = std::chrono::steady_clock::now();
    try {
        const auto samples = read_pcm_s16le_mono_16k(input_row.path);
        std::vector<float> old_samples;
        std::vector<float> window;
        int iteration = 0;

        for (std::size_t offset = 0;
             offset + static_cast<std::size_t>(kStepSamples) <= samples.size();
             offset += static_cast<std::size_t>(kStepSamples)) {
            const int take = std::min(
                static_cast<int>(old_samples.size()),
                std::max(0, kKeepSamples + kLengthSamples - kStepSamples));

            window.resize(static_cast<std::size_t>(take + kStepSamples));
            if (take > 0) {
                std::copy(old_samples.end() - take, old_samples.end(), window.begin());
            }
            std::copy(
                samples.begin() + static_cast<std::ptrdiff_t>(offset),
                samples.begin() + static_cast<std::ptrdiff_t>(offset + kStepSamples),
                window.begin() + take);
            old_samples = window;

            whisper_full_params params = whisper_full_default_params(WHISPER_SAMPLING_GREEDY);
            params.print_progress = false;
            params.print_special = false;
            params.print_realtime = false;
            params.print_timestamps = false;
            params.translate = false;
            params.single_segment = true;
            params.max_tokens = 0;
            params.language = "en";
            params.n_threads = kThreads;
            params.audio_ctx = 0;
            params.no_timestamps = true;
            params.no_context = true;
            params.temperature_inc = 0.0f;
            params.initial_prompt = nullptr;
            params.prompt_tokens = nullptr;
            params.prompt_n_tokens = 0;

            if (whisper_full(ctx, params, window.data(), static_cast<int>(window.size())) != 0) {
                result.status = "FAILED";
                result.failure_type = "WHISPER_FULL_ERROR";
                result.failure_message = "whisper_full returned non-zero";
                result.failure_iteration = iteration;
                break;
            }

            std::string iteration_text;
            const int segments = whisper_full_n_segments(ctx);
            for (int segment = 0; segment < segments; ++segment) {
                const char * text = whisper_full_get_segment_text(ctx, segment);
                if (text != nullptr) {
                    iteration_text += text;
                }
            }
            result.raw_lines.push_back(std::move(iteration_text));
            ++iteration;

            if ((iteration % kNewLineEvery) == 0) {
                if (window.size() < static_cast<std::size_t>(kKeepSamples)) {
                    fail("stream window shorter than frozen keep interval");
                }
                old_samples.assign(window.end() - kKeepSamples, window.end());
            }
        }

        result.stream_iteration_count = static_cast<int>(result.raw_lines.size());
        result.raw_transcript = reconstruct_stream_text(result.raw_lines);
        if (result.stream_iteration_count == 0 && result.status == "DECODED") {
            result.status = "FAILED";
            result.failure_type = "NO_STREAM_ITERATIONS";
            result.failure_message = "frozen input plus zero tail produced no complete 500 ms decode step";
            result.failure_iteration = 0;
        }
    } catch (const std::exception & error) {
        result.status = "FAILED";
        result.failure_type = "ADAPTER_INPUT_ERROR";
        result.failure_message = error.what();
        result.failure_iteration = result.stream_iteration_count;
        result.raw_transcript = reconstruct_stream_text(result.raw_lines);
    }

    const auto finished = std::chrono::steady_clock::now();
    result.decode_wall_seconds = std::chrono::duration<double>(finished - started).count();
    return result;
}

void write_result(std::ofstream & output, const InputRow & row, const DecodeResult & result) {
    output << "{\"utterance_id\":" << json_escape(row.utterance_id)
           << ",\"status\":" << json_escape(result.status)
           << ",\"raw_lines\":[";
    for (std::size_t i = 0; i < result.raw_lines.size(); ++i) {
        if (i != 0) {
            output << ',';
        }
        output << json_escape(result.raw_lines[i]);
    }
    output << "]"
           << ",\"raw_transcript\":" << json_escape(result.raw_transcript)
           << ",\"stream_iteration_count\":" << result.stream_iteration_count
           << ",\"decode_wall_seconds\":" << std::fixed << std::setprecision(9) << result.decode_wall_seconds
           << ",\"failure\":";
    if (result.status == "FAILED") {
        output << "{\"type\":" << json_escape(result.failure_type)
               << ",\"message\":" << json_escape(result.failure_message)
               << ",\"iteration\":" << result.failure_iteration << '}';
    } else {
        output << "null";
    }
    output << "}\n";
    if (!output.good()) {
        fail("failed writing adapter output");
    }
}

}  // namespace

int main(int argc, char ** argv) {
    try {
        const Args args = parse_args(argc, argv);
        const auto inputs = load_inputs(args.input_list);

        ggml_backend_load_all();
        whisper_context_params context_params = whisper_context_default_params();
        context_params.use_gpu = false;
        context_params.flash_attn = false;

        whisper_context * ctx = whisper_init_from_file_with_params(args.model.c_str(), context_params);
        if (ctx == nullptr) {
            std::cerr << "ADAPTER=FAIL: unable to initialize whisper context\n";
            return 2;
        }

        std::ofstream output(args.output, std::ios::binary | std::ios::trunc);
        if (!output.is_open()) {
            whisper_free(ctx);
            std::cerr << "ADAPTER=FAIL: unable to open output file\n";
            return 3;
        }

        for (const auto & row : inputs) {
            write_result(output, row, decode_one(ctx, row));
        }

        whisper_free(ctx);
        output.close();
        if (!output.good()) {
            std::cerr << "ADAPTER=FAIL: output close failed\n";
            return 4;
        }

        std::cout << "ADAPTER=PASS\n";
        std::cout << "ADAPTER_INPUTS=" << inputs.size() << "\n";
        std::cout << "ADAPTER_STEP_MS=" << kStepMs << "\n";
        std::cout << "ADAPTER_LENGTH_MS=" << kLengthMs << "\n";
        std::cout << "ADAPTER_KEEP_MS=" << kKeepMs << "\n";
        std::cout << "ADAPTER_FINAL_ZERO_SAMPLES=" << kFinalZeroSamples << "\n";
        return 0;
    } catch (const std::exception & error) {
        std::cerr << "ADAPTER=FAIL: " << error.what() << "\n";
        return 1;
    }
}
