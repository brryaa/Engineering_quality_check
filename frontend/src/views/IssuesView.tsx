import React, { useEffect, useState } from 'react';
import { api } from '../api/client';
import { EngineeringIssue } from '../types';
import { Badge } from '../components/Badge';
import { Search, AlertCircle, ShieldAlert, CheckCircle, HelpCircle } from 'lucide-react';

interface IssuesViewProps {
  selectedProgramId?: number;
  onNavigateToRootCause?: (issueId: number) => void;
}

export const IssuesView: React.FC<IssuesViewProps> = ({ selectedProgramId, onNavigateToRootCause }) => {
  const [issues, setIssues] = useState<EngineeringIssue[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [search, setSearch] = useState<string>('');
  const [severityFilter, setSeverityFilter] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [page, setPage] = useState<number>(1);
  const [selectedIssue, setSelectedIssue] = useState<EngineeringIssue | null>(null);

  const loadData = () => {
    setLoading(true);
    api.getIssues({
      page,
      page_size: 20,
      search,
      program_id: selectedProgramId,
      severity: severityFilter || undefined,
      status: statusFilter || undefined
    })
      .then((res) => {
        setIssues(res.items);
        setTotal(res.total);
      })
      .catch((err) => alert(`加载工程问题失败: ${err.message}`))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadData();
  }, [page, search, severityFilter, statusFilter, selectedProgramId]);

  const handleUpdateStatus = async (issueId: number, newStatus: string) => {
    try {
      await api.updateIssue(issueId, { status: newStatus as any });
      loadData();
      if (selectedIssue && selectedIssue.id === issueId) {
        setSelectedIssue({ ...selectedIssue, status: newStatus as any });
      }
    } catch (err: any) {
      alert(`更新状态失败: ${err.message}`);
    }
  };

  return (
    <div style={{ padding: '24px', maxWidth: '1440px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Header & Controls */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h1 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#f8fafc' }}>
            工程问题跟踪与 PRTS 闭环 ({total} 件)
          </h1>
          <p style={{ fontSize: '0.85rem', color: '#94a3b8' }}>
            开闭件与密封系统试制、试验验证与装车质量问题闭环跟踪
          </p>
        </div>
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
          <div style={{ position: 'relative' }}>
            <Search size={16} style={{ position: 'absolute', left: '10px', top: '10px', color: '#64748b' }} />
            <input
              type="text"
              placeholder="搜索问题编号/标题/责任人..."
              className="input-field"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{ paddingLeft: '32px', width: '220px' }}
            />
          </div>

          <select
            className="input-field"
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
          >
            <option value="">全部严重度等级</option>
            <option value="S1-Critical">S1-Critical 致命法规</option>
            <option value="S2-Major">S2-Major 重大功能</option>
            <option value="S3-Minor">S3-Minor 一般问题</option>
            <option value="S4-Cosmetic">S4-Cosmetic 轻微外观</option>
          </select>

          <select
            className="input-field"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="">全部问题状态</option>
            <option value="New">新建 New</option>
            <option value="Investigating">排查中 Investigating</option>
            <option value="Containment">已启动临时对策 Containment</option>
            <option value="RootCauseVerified">根因已确认 RootCauseVerified</option>
            <option value="ActionImplemented">对策已执行 ActionImplemented</option>
            <option value="Closed">已关闭 Closed</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="glass-panel" style={{ padding: '4px' }}>
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>问题编号 (PRTS)</th>
                <th>车型</th>
                <th>严重度</th>
                <th>问题简述</th>
                <th>零件编号</th>
                <th>发现阶段</th>
                <th>处理状态</th>
                <th>5-Why根因状态</th>
                <th>责任工程师</th>
                <th>目标关闭期</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={11} style={{ textAlign: 'center', padding: '30px', color: '#94a3b8' }}>
                    正在检索工程问题清单...
                  </td>
                </tr>
              ) : issues.length === 0 ? (
                <tr>
                  <td colSpan={11} style={{ textAlign: 'center', padding: '30px', color: '#94a3b8' }}>
                    无符合条件的工程问题记录
                  </td>
                </tr>
              ) : (
                issues.map((iss) => (
                  <tr key={iss.id}>
                    <td style={{ fontFamily: 'monospace', fontWeight: 600, color: '#38bdf8' }}>
                      {iss.issue_code}
                    </td>
                    <td><Badge label={iss.program_code || 'Global'} variant="indigo" /></td>
                    <td><Badge label={iss.severity} /></td>
                    <td style={{ fontWeight: 500, color: '#f8fafc', maxWidth: '240px' }}>
                      {iss.title}
                    </td>
                    <td style={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>{iss.part_number}</td>
                    <td><Badge label={iss.occurrence_phase} variant="slate" /></td>
                    <td><Badge label={iss.status} /></td>
                    <td>
                      {iss.has_root_cause ? (
                        <span style={{ color: '#34d399', fontSize: '0.75rem', fontWeight: 600 }}>✓ 已归零</span>
                      ) : (
                        <span style={{ color: '#fbbf24', fontSize: '0.75rem' }}>⏳ 待分析</span>
                      )}
                    </td>
                    <td style={{ fontSize: '0.8rem' }}>{iss.assignee}</td>
                    <td style={{ fontSize: '0.8rem', color: iss.status === 'Closed' ? '#34d399' : '#f8fafc' }}>
                      {iss.status === 'Closed' ? `已于 ${iss.closure_date} 关闭` : iss.due_date}
                    </td>
                    <td>
                      <button
                        className="btn-secondary"
                        style={{ padding: '4px 8px', fontSize: '0.75rem' }}
                        onClick={() => setSelectedIssue(iss)}
                      >
                        详情/推进
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
              disabled={issues.length < 20}
              onClick={() => setPage((p) => p + 1)}
            >
              下一页
            </button>
          </div>
        </div>
      </div>

      {/* Issue Detail & State Advancement Modal */}
      {selectedIssue && (
        <div className="modal-overlay">
          <div className="modal-content" style={{ padding: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div>
                <span style={{ fontSize: '0.8rem', color: '#38bdf8', fontWeight: 600 }}>{selectedIssue.issue_code}</span>
                <h2 style={{ fontSize: '1.15rem', fontWeight: 700, color: '#f8fafc' }}>
                  {selectedIssue.title}
                </h2>
              </div>
              <Badge label={selectedIssue.severity} />
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', fontSize: '0.85rem' }}>
              <div style={{ background: '#0f172a', padding: '12px', borderRadius: '8px' }}>
                <div style={{ color: '#94a3b8', fontSize: '0.75rem', marginBottom: '4px' }}>现象详细描述:</div>
                <div style={{ color: '#f8fafc' }}>{selectedIssue.description}</div>
              </div>

              <div style={{ background: '#0f172a', padding: '12px', borderRadius: '8px' }}>
                <div style={{ color: '#f59e0b', fontSize: '0.75rem', marginBottom: '4px', fontWeight: 600 }}>临时遏制措施 (Containment Action):</div>
                <div style={{ color: '#fde68a' }}>{selectedIssue.containment_action || '无紧急遏制方案'}</div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px' }}>
                <div style={{ background: '#0f172a', padding: '10px', borderRadius: '6px' }}>
                  <div style={{ color: '#94a3b8', fontSize: '0.7rem' }}>责任人</div>
                  <div style={{ fontWeight: 600, color: '#f8fafc' }}>{selectedIssue.assignee}</div>
                </div>
                <div style={{ background: '#0f172a', padding: '10px', borderRadius: '6px' }}>
                  <div style={{ color: '#94a3b8', fontSize: '0.7rem' }}>报告人</div>
                  <div style={{ fontWeight: 600, color: '#f8fafc' }}>{selectedIssue.reporter}</div>
                </div>
                <div style={{ background: '#0f172a', padding: '10px', borderRadius: '6px' }}>
                  <div style={{ color: '#94a3b8', fontSize: '0.7rem' }}>当前状态</div>
                  <Badge label={selectedIssue.status} />
                </div>
              </div>

              {/* Status advancement actions */}
              <div style={{ background: '#1e293b', border: '1px solid #334155', padding: '12px', borderRadius: '8px' }}>
                <div style={{ color: '#94a3b8', fontSize: '0.75rem', marginBottom: '8px' }}>快速变更流程状态:</div>
                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                  <button className="btn-secondary" onClick={() => handleUpdateStatus(selectedIssue.id, 'Containment')}>
                    启动遏制 (Containment)
                  </button>
                  <button className="btn-secondary" onClick={() => handleUpdateStatus(selectedIssue.id, 'ActionImplemented')}>
                    对策生效 (Implemented)
                  </button>
                  <button className="btn-primary" onClick={() => handleUpdateStatus(selectedIssue.id, 'Closed')}>
                    验证通过归零 (Closed)
                  </button>
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '16px' }}>
              <button className="btn-secondary" onClick={() => setSelectedIssue(null)}>
                关闭窗口
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
