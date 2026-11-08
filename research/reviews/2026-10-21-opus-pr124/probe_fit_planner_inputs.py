import sys, importlib.util, math
spec=importlib.util.spec_from_file_location('fp', sys.argv[1]); fp=importlib.util.module_from_spec(spec); sys.modules['fp']=fp; spec.loader.exec_module(fp)
cases={
 'nan_natural':([{'id':1,'start':0,'end':2}],[float('nan')],10),
 'inf_natural':([{'id':1,'start':0,'end':2}],[float('inf')],10),
 'negative_natural':([{'id':1,'start':0,'end':2}],[-3.0],10),
 'end_before_start':([{'id':1,'start':5,'end':2}],[1.0],10),
 'overlap':([{'id':1,'start':0,'end':4},{'id':2,'start':2,'end':5}],[3.0,3.0],10),
 'nan_total':([{'id':1,'start':0,'end':2}],[1.0],float('nan')),
}
for k,(s,n,t) in cases.items():
    try:
        p=fp.plan_fit(s,n,t); segs=[(x.__dict__) for x in p.segments] if hasattr(p,'segments') else p
        bad=any(isinstance(v,float) and not math.isfinite(v) for x in segs for v in x.values()) or (isinstance(p.total_duration,float) and not math.isfinite(p.total_duration))
        neg=any(isinstance(v,(int,float)) and v<0 for x in segs for kk,v in x.items() if 'dur' in kk or 'start' in kk or 'end' in kk)
        print(k,'ACCEPTED','nonfinite_output=',bad,'negative_timing=',neg,'total=',p.total_duration)
    except Exception as e: print(k,'REJECTED',type(e).__name__,str(e)[:60])
