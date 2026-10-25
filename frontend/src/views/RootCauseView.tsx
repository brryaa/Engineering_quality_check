import React, { useEffect, useState } from 'react';
import { api } from '../api/client';
import { RootCauseAnalysis } from '../types';
import { Badge } from '../components/Badge';
import { HelpCircle, GitCommit, CheckCircle2, AlertTriangle, Layers } from 'lucide-react';

export const RootCauseView: React.FC = () => {
  const [rootCauses, setRootCauses] = useState<RootCauseAnalysis[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedRc, setSelectedRc] = useState<RootCauseAnalysis | null>(null);
  const [page, setPage] = useState<number>(1);

  const loadData = () => {
    setLoading(true);
    api.getRootCauses({ page, page_size: 20 })
      .then((res) => {
        setRootCauses(res.items);
        setTotal(res.total);
        if (res.items.length > 0 && !selectedRc) {
          setSelectedRc(res.items[0]);
        }
      })
      .catch((err) => alert(`加载根因分析失败: ${err.message}`))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadData();
  }, [page]);

  return (
    <div style={{ padding: '24px', maxWidth: '1440px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Header */}
      <div>
        <h1 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#f8fafc' }}>
          故障根因分析 (5-Why & 因果鱼骨图归零)
        </h1>
        <p style={{ fontSize: '0.85rem', color: '#94a3b8' }}>
          运用 5-Why 递进逻辑链与人机料法环测 (Ishikawa 6M) 进行根本工程失效归因与试验再现验证
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '360px 1fr', gap: '20px', alignItems: 'flex-start' }}>
        {/* Left Side: Root Cause List */}
        <div className="glass-panel" style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div style={{ fontSize: '0.9rem', fontWeight: 600, color: '#f8fafc', borderBottom: '1px solid #334155', paddingBottom: '8px' }}>
            已归档根因案例 ({total})
          </div>
          {loading ? (
            <div style={{ padding: '20px', textAlign: 'center', color: '#94a3b8' }}>正在加载...</div>
          ) : rootCauses.length === 0 ? (
            <div style={{ padding: '20px', textAlign: 'center', color: '#94a3b8' }}>暂无根因归零分析记录</div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '720px', overflowY: 'auto' }}>
              {rootCauses.map((rc) => {
                const isSelected = selectedRc?.id === rc.id;
                return (
                  <div
                    key={rc.id}
                    onClick={() => setSelectedRc(rc)}
                    style={{
                      padding: '12px',
                      borderRadius: '8px',
                      background: isSelected ? 'rgba(2, 132, 199, 0.2)' : '#0f172a',
                      border: isSelected ? '1px solid #38bdf8' : '1px solid #334155',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontFamily: 'monospace', fontWeight: 600, color: '#38bdf8', fontSize: '0.8rem' }}>
                        {rc.issue_code}
                      </span>
                      <Badge label={rc.verification_result} />
                    </div>
                    <div style={{ fontSize: '0.85rem', color: '#f8fafc', fontWeight: 500, marginTop: '4px' }}>
                      {rc.direct_cause}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '4px' }}>
                      分析人: {rc.analyst} · {rc.analyzed_at}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Right Side: Visual 5-Why Chain & Fishbone diagram */}
        {selectedRc ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {/* 5-Why Visual Chain */}
            <div className="glass-panel" style={{ padding: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <h2 style={{ fontSize: '1rem', fontWeight: 600, color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <HelpCircle size={18} color="#38bdf8" />
                  5-Why 递进失效逻辑链 (Why 1 ~ Why 5)
                </h2>
                <Badge label={`分析方法: ${selectedRc.analysis_method}`} variant="indigo" />
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', position: 'relative' }}>
                {/* Direct Cause */}
                <div style={{ background: '#0f172a', border: '1px solid #334155', padding: '12px', borderRadius: '8px' }}>
                  <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#fb7185' }}>直接原因 (Direct Cause):</span>
                  <div style={{ color: '#f8fafc', marginTop: '2px' }}>{selectedRc.direct_cause}</div>
                </div>

                {/* Why 1 to 5 */}
                {[
                  { num: 'Why 1', text: selectedRc.why_1 },
                  { num: 'Why 2', text: selectedRc.why_2 },
                  { num: 'Why 3', text: selectedRc.why_3 },
                  { num: 'Why 4', text: selectedRc.why_4 },
                  { num: 'Why 5', text: selectedRc.why_5 }
                ].filter((w) => w.text).map((w, idx) => (
                  <div key={w.num} style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '12px',
                    padding: '12px',
                    background: 'rgba(30, 41, 59, 0.5)',
                    borderRadius: '8px',
                    borderLeft: '4px solid #0284c7'
                  }}>
                    <span style={{
                      background: '#0284c7',
                      color: 'white',
                      fontSize: '0.75rem',
                      fontWeight: 700,
                      padding: '2px 8px',
                      borderRadius: '4px',
                      whiteSpace: 'nowrap'
                    }}>
                      {w.num}
                    </span>
                    <div style={{ color: '#cbd5e1', fontSize: '0.85rem', lineHeight: '1.4' }}>
                      {w.text}
                    </div>
                  </div>
                ))}

                {/* Systemic Root Cause */}
                <div style={{
                  background: 'rgba(16, 185, 129, 0.1)',
                  border: '1px solid rgba(16, 185, 129, 0.3)',
                  padding: '14px',
                  borderRadius: '8px'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#34d399', fontWeight: 700, fontSize: '0.8rem' }}>
                    <CheckCircle2 size={16} /> 体系与设计根本原因 (Systemic Root Cause):
                  </div>
                  <div style={{ color: '#f8fafc', marginTop: '4px', fontSize: '0.9rem', fontWeight: 500 }}>
                    {selectedRc.systemic_root_cause}
                  </div>
                </div>
              </div>
            </div>

            {/* Fishbone 6M Categories */}
            <div className="glass-panel" style={{ padding: '20px' }}>
              <h2 style={{ fontSize: '1rem', fontWeight: 600, color: '#f8fafc', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Layers size={18} color="#fbbf24" />
                石川因果鱼骨图要素 (Ishikawa 6M Matrix)
              </h2>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px' }}>
                <div style={{ background: '#0f172a', padding: '10px', borderRadius: '6px', border: '1px solid #334155' }}>
                  <div style={{ color: '#38bdf8', fontSize: '0.75rem', fontWeight: 600 }}>👤 人 (Man)</div>
                  <div style={{ color: '#cbd5e1', fontSize: '0.8rem', marginTop: '4px' }}>{selectedRc.fishbone_man || '无异常'}</div>
                </div>
                <div style={{ background: '#0f172a', padding: '10px', borderRadius: '6px', border: '1px solid #334155' }}>
                  <div style={{ color: '#38bdf8', fontSize: '0.75rem', fontWeight: 600 }}>⚙️ 机 (Machine)</div>
                  <div style={{ color: '#cbd5e1', fontSize: '0.8rem', marginTop: '4px' }}>{selectedRc.fishbone_machine || '无异常'}</div>
                </div>
                <div style={{ background: '#0f172a', padding: '10px', borderRadius: '6px', border: '1px solid #334155' }}>
                  <div style={{ color: '#38bdf8', fontSize: '0.75rem', fontWeight: 600 }}>🧪 料 (Material)</div>
                  <div style={{ color: '#cbd5e1', fontSize: '0.8rem', marginTop: '4px' }}>{selectedRc.fishbone_material || '无异常'}</div>
                </div>
                <div style={{ background: '#0f172a', padding: '10px', borderRadius: '6px', border: '1px solid #334155' }}>
                  <div style={{ color: '#38bdf8', fontSize: '0.75rem', fontWeight: 600 }}>📋 法 (Method)</div>
                  <div style={{ color: '#cbd5e1', fontSize: '0.8rem', marginTop: '4px' }}>{selectedRc.fishbone_method || '无异常'}</div>
                </div>
                <div style={{ background: '#0f172a', padding: '10px', borderRadius: '6px', border: '1px solid #334155' }}>
                  <div style={{ color: '#38bdf8', fontSize: '0.75rem', fontWeight: 600 }}>📐 测 (Measurement)</div>
                  <div style={{ color: '#cbd5e1', fontSize: '0.8rem', marginTop: '4px' }}>{selectedRc.fishbone_measurement || '无异常'}</div>
                </div>
                <div style={{ background: '#0f172a', padding: '10px', borderRadius: '6px', border: '1px solid #334155' }}>
                  <div style={{ color: '#38bdf8', fontSize: '0.75rem', fontWeight: 600 }}>🌡️ 环 (Environment)</div>
                  <div style={{ color: '#cbd5e1', fontSize: '0.8rem', marginTop: '4px' }}>{selectedRc.fishbone_environment || '无异常'}</div>
                </div>
              </div>

              {/* Verification experiment */}
              <div style={{ background: '#0f172a', padding: '12px', borderRadius: '8px', marginTop: '14px' }}>
                <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#94a3b8' }}>验证试验方案与复现结论:</span>
                <div style={{ color: '#e2e8f0', fontSize: '0.85rem', marginTop: '2px' }}>{selectedRc.verification_method}</div>
                <div style={{ marginTop: '6px', fontSize: '0.8rem', color: '#34d399', fontWeight: 600 }}>
                  试验验证结论: 【{selectedRc.verification_result}】
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div style={{ padding: '40px', textAlign: 'center', color: '#94a3b8' }}>
            请在左侧选择具体工程问题的 5-Why 案例
          </div>
        )}
      </div>
    </div>
  );
};
