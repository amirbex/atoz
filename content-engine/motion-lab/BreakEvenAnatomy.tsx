// Optional Remotion adapter. Supply the same break-even-data.json object as the HTML scene.
// No Remotion dependency is vendored or required by the local SVG/FFmpeg pipeline.
import React from 'react';
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';

type BreakEvenData = {
  title_fa: string;
  evidence_label_fa: string;
  currency: string;
  formula: string;
  values: {
    fixed_cost: number;
    contribution_per_order: number;
    break_even_orders: number;
    period: string;
  };
};

const NAVY = '#0A1931';
const GOLD = '#FFB400';
const format = (value: number) => value.toLocaleString('fa-IR');

export const BreakEvenAnatomy: React.FC<{data: BreakEvenData}> = ({data}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const parts = [
    {title: 'هزینهٔ ثابت دوره', value: format(data.values.fixed_cost), unit: `${data.currency} · ${data.values.period}`},
    {title: 'حاشیهٔ مشارکت هر سفارش', value: format(data.values.contribution_per_order), unit: `${data.currency} · فرضی`},
    {title: 'رابطهٔ محاسبه', value: '÷', unit: 'هزینهٔ ثابت ÷ حاشیهٔ مشارکت'},
    {title: 'نقطهٔ سربه‌سر', value: format(data.values.break_even_orders), unit: `سفارش · ${data.values.period}`},
  ];
  return <AbsoluteFill style={{background: NAVY, color: 'white', fontFamily: 'Vazirmatn, sans-serif', padding: 92}}>
    <div style={{color: GOLD, fontSize: 28, letterSpacing: 3}}>ATOZ MOTION RECIPE · DATA-BOUND</div>
    <h1 style={{fontSize: 72, marginTop: 34, marginBottom: 16}}>{data.title_fa}</h1>
    <p style={{fontSize: 30, color: '#B8C5D5'}}>{data.evidence_label_fa}</p>
    <div style={{position: 'relative', flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 20}}>
      <div style={{position: 'absolute', right: 20, left: 20, top: '50%', height: 4, background: '#314864'}}>
        <div style={{height: '100%', width: `${interpolate(frame, [0, fps * 7], [0, 100], {extrapolateRight: 'clamp'})}%`, background: GOLD}} />
      </div>
      {parts.map((part, index) => {
        const start = index * fps * 1.55;
        const p = spring({frame: frame - start, fps, config: {damping: 18, stiffness: 90}});
        const opacity = interpolate(frame, [start, start + 12], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
        return <article key={part.title} style={{position: 'relative', zIndex: 1, opacity, transform: `translateY(${interpolate(p, [0, 1], [42, 0])}px) scale(${interpolate(p, [0, 1], [.92, 1])})`, width: '24%', minHeight: 245, padding: 28, border: `1px solid ${index === 3 ? GOLD : '#3B5271'}`, borderRadius: 22, background: '#12243E', textAlign: 'center'}}>
          <span style={{color: GOLD, fontSize: 24}}>0{index + 1}</span>
          <h2 style={{fontSize: 28, lineHeight: 1.65}}>{part.title}</h2>
          <strong style={{display: 'block', color: GOLD, fontSize: index === 2 ? 56 : 38}}>{part.value}</strong>
          <small style={{color: '#B1C0D4', fontSize: 18}}>{part.unit}</small>
        </article>;
      })}
    </div>
    <div style={{borderTop: '1px solid #31445F', paddingTop: 25, fontSize: 22, color: '#9EADC1'}}>{data.formula} · {data.evidence_label_fa}</div>
  </AbsoluteFill>;
};
