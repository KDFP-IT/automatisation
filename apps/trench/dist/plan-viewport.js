// Zoom is bounded only by finite floating-point arithmetic, never by a fixed UI range.
export function zoomPlanView(frame,zoom,factor,anchor=[450,260]){
 const next=zoom*factor;if(!frame||!Number.isFinite(next)||next<=0||!Number.isFinite(1/next)||!Number.isFinite(frame.scale*next))return {frame,zoom};
 const dx=(anchor[0]-450)*(1/next-1/zoom),dy=(anchor[1]-260)*(1/next-1/zoom);
 // Flatten transforms, avoiding an ever-growing chain on each wheel tick.
 const root=frame.root||frame,ox=(frame.offsetX||0)+dx,oy=(frame.offsetY||0)+dy;
 return {zoom:next,frame:{scale:root.scale,root,offsetX:ox,offsetY:oy,map:v=>{const q=root.map(v);return [q[0]+ox,q[1]+oy]},unmap:v=>root.unmap([v[0]-ox,v[1]-oy])}};
}
