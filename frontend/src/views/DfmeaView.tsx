import React, { useEffect, useState } from 'react';
import { api } from '../api/client';
import { DFMEA, Part } from '../types';
import { Badge } from '../components/Badge';
import { Plus, Search, AlertTriangle, ShieldCheck } from 'lucide-react';

interface DfmeaViewProps {
  selectedProgramId?: number;
}

export const DfmeaView: React.FC<DfmeaViewProps> = ({ selectedProgramId }) => {
  const [dfmeas, setDfmeas] = useState<DFMEA[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [search, setSearch] = useState<string>('');
  const [apFilter, setApFilter] = useState<string>('');
  const [minRpn, setMinRpn] = useState<string>('');
  const [page, setPage] = useState<number>(1);
  const [selectedDfmea, setSelectedDfmea] = useState<DFMEA | null>(null);

  const loadData = () => {
    setLoading(true);
    api.getDfmeas({
      page,
      page_size: 20,
      search,
      action_priority: apFilter || undefined,
      min_rpn: minRpn ? Number(minRpn) : undefined
    })
      .then((res) => {
        setDfmeas(res.items);
        setTotal(res.total);
      })
      .catch((err) => alert(`加载DFMEA失败: ${err.message}`))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadData();
  }, [page, search, apFilter, minRpn, selectedProgramId]);

  return (
    <div style={{ padding: '24px', maxWidth: '1440px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Header & Controls */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h1 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#f8fafc' }}>
            DFMEA 设计潜在失效模式与后果分析 ({total} 项)
          </h1>
          <p style={{ fontSize: '0.85rem', color: '#94a3b8' }}>
            遵循 AIAG & VDA 2019 第1版 AP 行动优先级标准 (严重度 S · 频度 O · 探测度 D · RPN)
          </p>
        </div>
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
          <div style={{ position: 'relative' }}>
            <Search size={16} style={{ position: 'absolute', left: '10px', top: '10px', color: '#64748b' }} />
            <input
              type="text"
              placeholder="搜索失效模式/原因/功能..."
              className="input-field"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{ paddingLeft: '32px', width: '220px' }}
            />
          </div>

          <select
            className="input-field"
            value={apFilter}
            onChange={(e) => setApFilter(e.target.value)}
          >
            <option value="">全部 AP 优先级</option>
            <option value="High">🔴 高优先级 High AP (必改)</option>
            <option value="Medium">🟡 中优先级 Medium AP (预防)</option>
            <option value="Low">🟢 低优先级 Low AP (可接受)</option>
          </select>

          <select
            className="input-field"
            value={minRpn}
            onChange={(e) => setMinRpn(e.target.value)}
          >
            <option value="">全部 RPN 阈值</option>
            <option value="100">RPN ≥ 100 重点风险</option>
            <option value="200">RPN ≥ 200 高度危险</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="glass-panel" style={{ padding: '4px' }}>
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>FMEA编号</th>
                <th>关联零件号</th>
                <th>潜在失效模式 (Failure Mode)</th>
                <th>潜在失效后果 (Effect)</th>
                <th>严重度 (S)</th>
                <th>起因机理 (Cause)</th>
                <th>频度 (O)</th>
                <th>探测度 (D)</th>
                <th>RPN</th>
                <th>AP 行动优先级</th>
                <th>整改进度</th>
                <th>详情</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={12} style={{ textAlign: 'center', padding: '30px', color: '#94a3b8' }}>
                    正在检索DFMEA矩阵...
                  </td>
                </tr>
              ) : dfmeas.length === 0 ? (
                <tr>
                  <td colSpan={12} style={{ textAlign: 'center', padding: '30px', color: '#94a3b8' }}>
                    无符合筛选条件的 DFMEA 记录
                  </td>
                </tr>
              ) : (
                dfmeas.map((row) => (
                  <tr key={row.id}>
                    <td style={{ fontFamily: 'monospace', fontWeight: 600, color: '#38bdf8' }}>
                      {row.fmea_code}
                    </td>
                    <td style={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>
                      {row.part_number}
                    </td>
                    <td style={{ fontWeight: 500, color: '#f8fafc', maxWidth: '220px' }}>
                      {row.failure_mode}
                    </td>
                    <td style={{ fontSize: '0.8rem', color: '#cbd5e1', maxWidth: '200px' }}>
                      {row.failure_effect}
                    </td>
                    <td style={{ fontWeight: 700, color: row.severity >= 8 ? '#f43f5e' : '#fbbf24', textAlign: 'center' }}>
                      {row.severity}
                    </td>
                    <td style={{ fontSize: '0.8rem', color: '#94a3b8', maxWidth: '200px' }}>
                      {row.cause_mechanism}
                    </td>
                    <td style={{ fontWeight: 700, textAlign: 'center' }}>{row.occurrence}</td>
                    <td style={{ fontWeight: 700, textAlign: 'center' }}>{row.detection}</td>
                    <td style={{ fontWeight: 800, color: row.rpn >= 150 ? '#f43f5e' : row.rpn >= 80 ? '#fbbf24' : '#34d399', textAlign: 'center' }}>
                      {row.rpn}
                    </td>
                    <td style={{ textAlign: 'center' }}>
                      <Badge label={row.action_priority} />
                    </td>
                    <td>
                      <Badge label={row.action_status} />
                    </td>
                    <td>
                      <button
                        className="btn-secondary"
                        style={{ padding: '4px 8px', fontSize: '0.75rem' }}
                        onClick={() => setSelectedDfmea(row)}
                      >
                        审查措施
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 16px' }}>
          <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
            第 {page} 页，共 {total} 条数据
          </span>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              className="btn-secondary"
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
            >
              上一页
            </button>
            <button
              className="btn-secondary"
              disabled={dfmeas.length < 20}
              onClick={() => setPage((p) => p + 1)}
            >
              下一页
            </button>
          </div>
        </div>
      </div>

      {/* Detail / Review Modal */}
      {selectedDfmea && (
        <div className="modal-overlay">
          <div className="modal-content" style={{ padding: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div>
                <span style={{ fontSize: '0.8rem', color: '#38bdf8', fontWeight: 600 }}>{selectedDfmea.fmea_code}</span>
                <h2 style={{ fontSize: '1.15rem', fontWeight: 700, color: '#f8fafc' }}>
                  DFMEA 风险措施审查
                </h2>
              </div>
              <Badge label={`AP: ${selectedDfmea.action_priority}`} />
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', fontSize: '0.85rem' }}>
              <div style={{ background: '#0f172a', padding: '12px', borderRadius: '8px' }}>
                <div style={{ color: '#94a3b8', fontSize: '0.75rem', marginBottom: '4px' }}>项目与功能:</div>
                <div style={{ color: '#f8fafc' }}>{selectedDfmea.item_function}</div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div style={{ background: '#0f172a', padding: '12px', borderRadius: '8px' }}>
                  <div style={{ color: '#fb7185', fontSize: '0.75rem', marginBottom: '4px' }}>失效模式:</div>
                  <div style={{ color: '#f8fafc' }}>{selectedDfmea.failure_mode}</div>
                </div>
                <div style={{ background: '#0f172a', padding: '12px', borderRadius: '8px' }}>
                  <div style={{ color: '#fbbf24', fontSize: '0.75rem', marginBottom: '4px' }}>失效机理/原因:</div>
                  <div style={{ color: '#f8fafc' }}>{selectedDfmea.cause_mechanism}</div>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '8px', textAlign: 'center' }}>
                <div style={{ background: '#0f172a', padding: '8px', borderRadius: '6px' }}>
                  <div style={{ color: '#94a3b8', fontSize: '0.7rem' }}>严重度(S)</div>
                  <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#f43f5e' }}>{selectedDfmea.severity}</div>
                </div>
                <div style={{ background: '#0f172a', padding: '8px', borderRadius: '6px' }}>
                  <div style={{ color: '#94a3b8', fontSize: '0.7rem' }}>频度(O)</div>
                  <div style={{ fontSize: '1.25rem', fontWeight: 700 }}>{selectedDfmea.occurrence}</div>
                </div>
                <div style={{ background: '#0f172a', padding: '8px', borderRadius: '6px' }}>
                  <div style={{ color: '#94a3b8', fontSize: '0.7rem' }}>探测度(D)</div>
                  <div style={{ fontSize: '1.25rem', fontWeight: 700 }}>{selectedDfmea.detection}</div>
                </div>
                <div style={{ background: '#0f172a', padding: '8px', borderRadius: '6px' }}>
                  <div style={{ color: '#94a3b8', fontSize: '0.7rem' }}>当前 RPN</div>
                  <div style={{ fontSize: '1.25rem', fontWeight: 800, color: '#fbbf24' }}>{selectedDfmea.rpn}</div>
                </div>
              </div>

              <div style={{ background: '#0f172a', padding: '12px', borderRadius: '8px' }}>
                <div style={{ color: '#38bdf8', fontSize: '0.75rem', marginBottom: '4px' }}>当前预防控制 (Prevention Control):</div>
                <div style={{ color: '#e2e8f0' }}>{selectedDfmea.prevention_control}</div>
              </div>

              <div style={{ background: '#0f172a', padding: '12px', borderRadius: '8px' }}>
                <div style={{ color: '#38bdf8', fontSize: '0.75rem', marginBottom: '4px' }}>当前探测控制 (Detection Control):</div>
                <div style={{ color: '#e2e8f0' }}>{selectedDfmea.detection_control}</div>
              </div>

              <div style={{ background: '#172554', border: '1px solid #1e40af', padding: '12px', borderRadius: '8px' }}>
                <div style={{ color: '#60a5fa', fontWeight: 600, marginBottom: '4px' }}>建议纠正预防措施 (Recommended Action):</div>
                <div style={{ color: '#f8fafc' }}>{selectedDfmea.recommended_action || '待指定'}</div>
                <div style={{ marginTop: '8px', display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: '#93c5fd' }}>
                  <span>责任工程师: {selectedDfmea.action_owner || '待分配'}</span>
                  <span>目标节点: {selectedDfmea.target_date || '未指定'}</span>
                  <span>整改后 RPN: {selectedDfmea.post_rpn || '待验证重新评估'}</span>
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '16px' }}>
              <button className="btn-secondary" onClick={() => setSelectedDfmea(null)}>
                关闭
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
