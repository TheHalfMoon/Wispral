#include "whisper.h"

#include <algorithm>
#include <cctype>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace fs = std::filesystem;

namespace {

constexpr int kSampleRate = 16000;
constexpr int kStepSamples = 8000;       // 500 ms
constexpr int kLengthSamples = 80000;    // 5000 ms
constexpr int kKeepSamples = 3200;       // 200 ms
constexpr int kFinalZeroSamples = 10560; // 660 ms
constexpr int kThreads = 4;
constexpr int kNewLineEvery = 9;         // max(1, 5000 / 500 - 1)

struct InputRow {
    std::string utterance_id;
    fs::path wav_path;
};

struct EventMeta {
    int index = 0;
    std::size_t feed_start = 0;
    std::size_t feed_end = 0;
    std::size_t window_samples = 0;
    bool commit_boundary = false;
};

std::uint16_t read_u16_le(const std::vector<std::uint8_t>& bytes, std::size_t offset) {
    if (offset + 2 > bytes.size()) {
        throw std::runtime_error("truncated WAV u16 field");
    }
    return static_cast<std::uint16_t>(bytes[offset]) |
           (static_cast<std::uint16_t>(bytes[offset + 1]) << 8U);
}

std::uint32_t read_u32_le(const std::vector<std::uint8_t>& bytes, std::size_t offset) {
    if (offset + 4 > bytes.size()) {
        throw std::runtime_error("truncated WAV u32 field");
    }
    return static_cast<std::uint32_t>(bytes[offset]) |
           (static_cast<std::uint32_t>(bytes[offset + 1]) << 8U) |
           (static_cast<std::uint32_t>(bytes[offset + 2]) << 16U) |
           (static_cast<std::uint32_t>(bytes[offset + 3]) << 24U);
}

bool chunk_id_is(const std::vector<std::uint8_t>& bytes, std::size_t offset, const char* expected) {
    return offset + 4 <= bytes.size() && std::memcmp(bytes.data() + offset, expected, 4) == 0;
}

std::vector<float> read_pcm16_mono_16k(const fs::path& path) {
    std::ifstream input(path, std::ios::binary);
    if (!input) {
        throw std::runtime_error("unable to open canonical WAV: " + path.string());
    }
    input.seekg(0, std::ios::end);
    const std::streamoff length = input.tellg();
    if (length < 44 || length > static_cast<std::streamoff>(64 * 1024 * 1024)) {
        throw std::runtime_error("canonical WAV size is outside bounded RIFF range: " + path.string());
    }
    input.seekg(0, std::ios::beg);
    std::vector<std::uint8_t> bytes(static_cast<std::size_t>(length));
    input.read(reinterpret_cast<char*>(bytes.data()), static_cast<std::streamsize>(bytes.size()));
    if (!input) {
        throw std::runtime_error("unable to read canonical WAV bytes: " + path.string());
    }

    if (!chunk_id_is(bytes, 0, "RIFF") || !chunk_id_is(bytes, 8, "WAVE")) {
        throw std::runtime_error("canonical WAV RIFF/WAVE header drift: " + path.string());
    }
    const std::uint32_t riff_size = read_u32_le(bytes, 4);
    if (static_cast<std::uint64_t>(riff_size) + 8U > bytes.size()) {
        throw std::runtime_error("canonical WAV RIFF size exceeds file: " + path.string());
    }

    bool saw_fmt = false;
    bool saw_data = false;
    std::size_t data_offset = 0;
    std::size_t data_size = 0;
    std::size_t offset = 12;
    while (offset + 8 <= bytes.size()) {
        const std::uint32_t chunk_size = read_u32_le(bytes, offset + 4);
        const std::size_t payload = offset + 8;
        const std::uint64_t end64 = static_cast<std::uint64_t>(payload) + chunk_size;
        if (end64 > bytes.size()) {
            throw std::runtime_error("canonical WAV chunk exceeds file: " + path.string());
        }
        const std::size_t end = static_cast<std::size_t>(end64);

        if (chunk_id_is(bytes, offset, "fmt ")) {
            if (saw_fmt || chunk_size < 16) {
                throw std::runtime_error("canonical WAV fmt chunk drift: " + path.string());
            }
            saw_fmt = true;
            const std::uint16_t audio_format = read_u16_le(bytes, payload + 0);
            const std::uint16_t channels = read_u16_le(bytes, payload + 2);
            const std::uint32_t sample_rate = read_u32_le(bytes, payload + 4);
            const std::uint16_t block_align = read_u16_le(bytes, payload + 12);
            const std::uint16_t bits_per_sample = read_u16_le(bytes, payload + 14);
            if (audio_format != 1 || channels != 1 || sample_rate != kSampleRate ||
                block_align != 2 || bits_per_sample != 16) {
                throw std::runtime_error("canonical WAV PCM_S16LE mono/16k shape drift: " + path.string());
            }
        } else if (chunk_id_is(bytes, offset, "data")) {
            if (saw_data || chunk_size == 0 || (chunk_size % 2U) != 0U) {
                throw std::runtime_error("canonical WAV data chunk drift: " + path.string());
            }
            saw_data = true;
            data_offset = payload;
            data_size = chunk_size;
        }

        offset = end + (chunk_size & 1U);
    }

    if (!saw_fmt || !saw_data) {
        throw std::runtime_error("canonical WAV missing fmt/data chunk: " + path.string());
    }

    std::vector<float> samples;
    samples.reserve(data_size / 2U);
    for (std::size_t pos = data_offset; pos < data_offset + data_size; pos += 2) {
        const std::uint16_t raw = static_cast<std::uint16_t>(bytes[pos]) |
                                  (static_cast<std::uint16_t>(bytes[pos + 1]) << 8U);
        const std::int16_t signed_sample = static_cast<std::int16_t>(raw);
        samples.push_back(static_cast<float>(signed_sample) / 32768.0F);
    }
    if (samples.empty()) {
        throw std::runtime_error("canonical WAV contains no PCM samples: " + path.string());
    }
    return samples;
}

bool valid_utterance_id(const std::string& value) {
    if (value.empty() || value.size() > 128) {
        return false;
    }
    for (const unsigned char ch : value) {
        if (!(std::isalnum(ch) || ch == '-' || ch == '_')) {
            return false;
        }
    }
    return true;
}

std::vector<InputRow> read_input_list(const fs::path& path) {
    std::ifstream input(path);
    if (!input) {
        throw std::runtime_error("unable to open adapter input list: " + path.string());
    }
    std::vector<InputRow> rows;
    std::string line;
    while (std::getline(input, line)) {
        if (line.empty()) {
            continue;
        }
        const std::size_t tab = line.find('\t');
        if (tab == std::string::npos || line.find('\t', tab + 1) != std::string::npos) {
            throw std::runtime_error("adapter input list must contain exactly one tab per row");
        }
        InputRow row{line.substr(0, tab), fs::path(line.substr(tab + 1))};
        if (!valid_utterance_id(row.utterance_id) || row.wav_path.empty()) {
            throw std::runtime_error("adapter input row identity/path drift");
        }
        rows.push_back(std::move(row));
    }
    if (rows.empty() || rows.size() > 1000) {
        throw std::runtime_error("adapter input list cardinality outside bounded range");
    }
    return rows;
}

void write_text_file(const fs::path& path, const std::string& value) {
    std::ofstream output(path, std::ios::binary);
    if (!output) {
        throw std::runtime_error("unable to create adapter output: " + path.string());
    }
    output.write(value.data(), static_cast<std::streamsize>(value.size()));
    if (!output) {
        throw std::runtime_error("unable to write adapter output: " + path.string());
    }
}

std::string decode_window(whisper_context* ctx, const std::vector<float>& window) {
    whisper_full_params wparams = whisper_full_default_params(WHISPER_SAMPLING_GREEDY);
    wparams.print_progress = false;
    wparams.print_special = false;
    wparams.print_realtime = false;
    wparams.print_timestamps = false;
    wparams.translate = false;
    wparams.single_segment = true;
    wparams.max_tokens = 0;
    wparams.language = "en";
    wparams.n_threads = kThreads;
    wparams.beam_search.beam_size = -1;
    wparams.audio_ctx = 0;
    wparams.tdrz_enable = false;
    wparams.temperature_inc = 0.0F;
    wparams.prompt_tokens = nullptr;
    wparams.prompt_n_tokens = 0;

    if (whisper_full(ctx, wparams, window.data(), static_cast<int>(window.size())) != 0) {
        throw std::runtime_error("whisper_full returned non-zero");
    }
    std::string text;
    const int segment_count = whisper_full_n_segments(ctx);
    for (int segment = 0; segment < segment_count; ++segment) {
        const char* part = whisper_full_get_segment_text(ctx, segment);
        if (part != nullptr) {
            text += part;
        }
    }
    return text;
}

void write_failure(const fs::path& utterance_dir, int step_index, const std::string& message) {
    std::ofstream output(utterance_dir / "failure.tsv");
    if (!output) {
        throw std::runtime_error("unable to create adapter failure record");
    }
    output << "WHISPER_FULL_ERROR\t" << step_index << "\t" << message << "\n";
}

void process_utterance(whisper_context* ctx, const InputRow& row, const fs::path& output_root) {
    const std::vector<float> speech = read_pcm16_mono_16k(row.wav_path);
    std::vector<float> feed = speech;
    feed.insert(feed.end(), kFinalZeroSamples, 0.0F);

    const std::size_t full_steps = feed.size() / static_cast<std::size_t>(kStepSamples);
    const std::size_t processed_feed_samples = full_steps * static_cast<std::size_t>(kStepSamples);
    if (processed_feed_samples < speech.size()) {
        throw std::runtime_error("finalization zero suffix failed to cover all speech samples");
    }
    const std::size_t unconsumed_suffix_samples = feed.size() - processed_feed_samples;
    if (unconsumed_suffix_samples > static_cast<std::size_t>(kFinalZeroSamples)) {
        throw std::runtime_error("unconsumed feed remainder contains non-suffix audio");
    }

    const fs::path utterance_dir = output_root / row.utterance_id;
    fs::create_directories(utterance_dir);
    std::ofstream events_meta(utterance_dir / "events.tsv");
    if (!events_meta) {
        throw std::runtime_error("unable to create adapter event metadata");
    }

    std::vector<float> old;
    int n_iter = 0;
    bool failed = false;
    for (std::size_t step = 0; step < full_steps; ++step) {
        const std::size_t feed_start = step * static_cast<std::size_t>(kStepSamples);
        const std::size_t feed_end = feed_start + static_cast<std::size_t>(kStepSamples);
        const std::size_t max_take = static_cast<std::size_t>(kKeepSamples + kLengthSamples - kStepSamples);
        const std::size_t take = std::min(old.size(), max_take);

        std::vector<float> window;
        window.reserve(take + static_cast<std::size_t>(kStepSamples));
        if (take > 0) {
            window.insert(window.end(), old.end() - static_cast<std::ptrdiff_t>(take), old.end());
        }
        window.insert(window.end(), feed.begin() + static_cast<std::ptrdiff_t>(feed_start),
                      feed.begin() + static_cast<std::ptrdiff_t>(feed_end));
        old = window;

        try {
            const std::string text = decode_window(ctx, window);
            char event_name[32];
            std::snprintf(event_name, sizeof(event_name), "event-%06d.txt", n_iter);
            write_text_file(utterance_dir / event_name, text);
        } catch (const std::exception& error) {
            write_failure(utterance_dir, n_iter, error.what());
            failed = true;
            break;
        }

        ++n_iter;
        const bool commit_boundary = (n_iter % kNewLineEvery) == 0;
        events_meta << (n_iter - 1) << '\t'
                    << feed_start << '\t'
                    << feed_end << '\t'
                    << window.size() << '\t'
                    << (commit_boundary ? 1 : 0) << '\n';

        if (commit_boundary) {
            if (old.size() < static_cast<std::size_t>(kKeepSamples)) {
                throw std::runtime_error("stream keep window underflow");
            }
            old = std::vector<float>(old.end() - kKeepSamples, old.end());
        }
    }

    std::ofstream meta(utterance_dir / "meta.tsv");
    if (!meta) {
        throw std::runtime_error("unable to create adapter utterance metadata");
    }
    meta << "status\t" << (failed ? "FAILED" : "DECODED") << '\n';
    meta << "speech_samples\t" << speech.size() << '\n';
    meta << "feed_total_samples\t" << feed.size() << '\n';
    meta << "processed_feed_samples\t" << processed_feed_samples << '\n';
    meta << "unconsumed_suffix_samples\t" << unconsumed_suffix_samples << '\n';
    meta << "step_count\t" << n_iter << '\n';
    meta << "step_samples\t" << kStepSamples << '\n';
    meta << "length_samples\t" << kLengthSamples << '\n';
    meta << "keep_samples\t" << kKeepSamples << '\n';
    meta << "final_zero_samples\t" << kFinalZeroSamples << '\n';
    meta << "n_new_line\t" << kNewLineEvery << '\n';
}

struct Args {
    fs::path model;
    fs::path input_list;
    fs::path output_dir;
};

Args parse_args(int argc, char** argv) {
    Args args;
    for (int i = 1; i < argc; ++i) {
        const std::string arg = argv[i];
        if ((arg == "--model" || arg == "--input-list" || arg == "--output-dir") && i + 1 >= argc) {
            throw std::runtime_error("adapter argument requires a value: " + arg);
        }
        if (arg == "--model") {
            args.model = argv[++i];
        } else if (arg == "--input-list") {
            args.input_list = argv[++i];
        } else if (arg == "--output-dir") {
            args.output_dir = argv[++i];
        } else {
            throw std::runtime_error("unknown adapter argument: " + arg);
        }
    }
    if (args.model.empty() || args.input_list.empty() || args.output_dir.empty()) {
        throw std::runtime_error("--model, --input-list, and --output-dir are required");
    }
    return args;
}

} // namespace

int main(int argc, char** argv) {
    try {
        const Args args = parse_args(argc, argv);
        const std::vector<InputRow> inputs = read_input_list(args.input_list);
        if (fs::exists(args.output_dir)) {
            fs::remove_all(args.output_dir);
        }
        fs::create_directories(args.output_dir);

        whisper_context_params context_params = whisper_context_default_params();
        context_params.use_gpu = false;
        context_params.flash_attn = false;
        whisper_context* ctx = whisper_init_from_file_with_params(args.model.string().c_str(), context_params);
        if (ctx == nullptr) {
            throw std::runtime_error("failed to initialize pinned whisper.cpp context");
        }

        try {
            for (const InputRow& row : inputs) {
                process_utterance(ctx, row, args.output_dir);
            }
        } catch (...) {
            whisper_free(ctx);
            throw;
        }
        whisper_free(ctx);
        std::cout << "B2E03_ADAPTER=PASS\n";
        std::cout << "B2E03_ADAPTER_INPUTS=" << inputs.size() << "\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "B2E03_ADAPTER=FAIL: " << error.what() << "\n";
        return 1;
    }
}
