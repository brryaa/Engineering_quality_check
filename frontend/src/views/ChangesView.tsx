import React, { useEffect, useState } from 'react';
import { api } from '../api/client';
import { EngineeringChange, Program } from '../types';
import { Badge } from '../components/Badge';
import { Plus, Search, GitPullRequest, ArrowRight, CheckCircle2, Clock } from 'lucide-react';

interface ChangesViewProps {
  selectedProgramId?: number;
  programs: Program[];
}

export const ChangesView: React.FC<ChangesViewProps> = ({ selectedProgramId, programs }) => {
  const [changes, setChanges] = useState<EngineeringChange[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [search, setSearch] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [page, setPage] = useState<number>(1);
  const [selectedChange, setSelectedChange] = useState<EngineeringChange | null>(null);

  const loadData = () => {
    setLoading(true);
    api.getChanges({
      page,
      page_size: 20,
      search,
      program_id: selectedProgramId,
      approval_status: statusFilter || undefined
    })
      .then((res) => {
        setChanges(res.items);
        setTotal(res.total);
      })
      .catch((err) => alert(`加载工程变更失败: ${err.message}`))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadData();
  }, [page, search, statusFilter, selectedProgramId]);

  const handleApprove = async (changeId: number) => {
    try {
      await api.updateChange(changeId, {
        approval_status: 'Approved',
        approver: 'Dr. Wei Chen'
      });
      loadData();
      if (selectedChange && selectedChange.id === changeId) {
        setSelectedChange({ ...selectedChange, approval_status: 'Approved', approver: 'Dr. Wei Chen' });
      }
    } catch (err: any) {
      alert(`审批失败: ${err.message}`);
    }
  };

  const handleImplement = async (changeId: number) => {
    try {
      await api.updateChange(changeId, {
        approval_status: 'Implemented'
      });
      loadData();
      if (selectedChange && selectedChange.id === changeId) {
        setSelectedChange({ ...selectedChange, approval_status: 'Implemented' });
      }
    } catch (err: any) {
      alert(`变更下发失败: ${err.message}`);
    }
  };

  return (
    <div style={{ padding: '24px', maxWidth: '1440px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Header & Controls */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h1 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#f8fafc' }}>
            工程变更管理 (ECR / ECO 闭环控制 - {total} 件)
          </h1>
          <p style={{ fontSize: '0.85rem', color: '#94a3b8' }}>
            设计优化、材料替换、模具修整与公差放宽变更流程，自动联动版本迭代与模具周期
          </p>
        </div>
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
          <div style={{ position: 'relative' }}>
            <Search size={16} style={{ position: 'absolute', left: '10px', top: '10px', color: '#64748b' }} />
            <input
              type="text"
              placeholder="搜索ECR单号/变更主题/发起人..."
              className="input-field"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{ paddingLeft: '32px', width: '220px' }}
            />
          </div>

          <select
            className="input-field"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="">全部审批状态</option>
            <option value="Draft">草稿 Draft</option>
            <option value="Review-Eng">工程评审 Review-Eng</option>
            <option value="Review-CostTooling">成本模具评审 CostTooling</option>
            <option value="Approved">已批准 Approved</option>
            <option value="Implemented">已下发执行 Implemented</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="glass-panel" style={{ padding: '4px' }}>
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>ECR单号</th>
                <th>车型</th>
                <th>受影响零件号</th>
                <th>变更类型</th>
                <th>变更主题与原因</th>
                <th>版本升级 (Rev)</th>
                <th>单车成本变动</th>
                <th>模具周期</th>
                <th>法规重认证</th>
                <th>审批状态</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={11} style={{ textAlign: 'center', padding: '30px', color: '#94a3b8' }}>
                    正在检索工程变更台账...
                  </td>
                </tr>
              ) : changes.length === 0 ? (
                <tr>
                  <td colSpan={11} style={{ textAlign: 'center', padding: '30px', color: '#94a3b8' }}>
                    无符合条件的工程变更记录
                  </td>
                </tr>
              ) : (
                changes.map((ecr) => (
                  <tr key={ecr.id}>
                    <td style={{ fontFamily: 'monospace', fontWeight: 600, color: '#38bdf8' }}>
                      {ecr.change_code}
                    </td>
                    <td><Badge label={ecr.program_code || 'Global'} variant="indigo" /></td>
                    <td style={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>{ecr.part_number}</td>
                    <td><Badge label={ecr.change_type} variant="slate" /></td>
                    <td style={{ maxWidth: '240px' }}>
                      <div style={{ fontWeight: 500, color: '#f8fafc' }}>{ecr.title}</div>
                      <div style={{ fontSize: '0.75rem', color: '#94a3b8', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {ecr.reason}
                      </div>
                    </td>
                    <td>
                      <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', fontFamily: 'monospace', fontSize: '0.8rem' }}>
                        {ecr.pre_change_rev} <ArrowRight size={12} color="#38bdf8" /> <strong style={{ color: '#34d399' }}>{ecr.post_change_rev}</strong>
                      </span>
                    </td>
                    <td style={{ fontWeight: 600, color: ecr.cost_impact_rmb > 0 ? '#fb7185' : ecr.cost_impact_rmb < 0 ? '#34d399' : '#cbd5e1' }}>
                      {ecr.cost_impact_rmb > 0 ? `+¥${ecr.cost_impact_rmb}` : `¥${ecr.cost_impact_rmb}`}
                    </td>
                    <td style={{ fontSize: '0.8rem' }}>{ecr.tooling_lead_weeks} 周</td>
                    <td style={{ fontSize: '0.75rem' }}>
                      {ecr.requires_homologation ? (
                        <span style={{ color: '#f43f5e', fontWeight: 600 }}>需要公告认证</span>
                      ) : (
                        <span style={{ color: '#64748b' }}>无需公告</span>
                      )}
                    </td>
                    <td><Badge label={ecr.approval_status} /></td>
                    <td>
                      <button
                        className="btn-secondary"
                        style={{ padding: '4px 8px', fontSize: '0.75rem' }}
                        onClick={() => setSelectedChange(ecr)}
                      >
                        详情/审批
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
              disabled={changes.length < 20}
              onClick={() => setPage((p) => p + 1)}
            >
              下一页
            </button>
          </div>
        </div>
      </div>

      {/* Change Order Review Modal */}
      {selectedChange && (
        <div className="modal-overlay">
          <div className="modal-content" style={{ padding: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div>
                <span style={{ fontSize: '0.8rem', color: '#38bdf8', fontWeight: 600 }}>{selectedChange.change_code}</span>
                <h2 style={{ fontSize: '1.15rem', fontWeight: 700, color: '#f8fafc' }}>
                  {selectedChange.title}
                </h2>
              </div>
              <Badge label={selectedChange.approval_status} />
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', fontSize: '0.85rem' }}>
              <div style={{ background: '#0f172a', padding: '12px', borderRadius: '8px' }}>
                <div style={{ color: '#94a3b8', fontSize: '0.75rem', marginBottom: '4px' }}>变更起因与必要性说明:</div>
                <div style={{ color: '#f8fafc' }}>{selectedChange.reason}</div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px' }}>
                <div style={{ background: '#0f172a', padding: '10px', borderRadius: '6px' }}>
                  <div style={{ color: '#94a3b8', fontSize: '0.7rem' }}>版本升级</div>
                  <div style={{ fontWeight: 700, color: '#38bdf8' }}>{selectedChange.pre_change_rev} → {selectedChange.post_change_rev}</div>
                </div>
                <div style={{ background: '#0f172a', padding: '10px', borderRadius: '6px' }}>
                  <div style={{ color: '#94a3b8', fontSize: '0.7rem' }}>单车成本增减</div>
                  <div style={{ fontWeight: 700, color: selectedChange.cost_impact_rmb > 0 ? '#fb7185' : '#34d399' }}>
                    ¥{selectedChange.cost_impact_rmb}
                  </div>
                </div>
                <div style={{ background: '#0f172a', padding: '10px', borderRadius: '6px' }}>
                  <div style={{ color: '#94a3b8', fontSize: '0.7rem' }}>模具工装周期</div>
                  <div style={{ fontWeight: 700, color: '#f8fafc' }}>{selectedChange.tooling_lead_weeks} 周</div>
                </div>
              </div>

              {/* Workflow Stepper */}
              <div style={{ background: '#0f172a', padding: '14px', borderRadius: '8px' }}>
                <div style={{ color: '#94a3b8', fontSize: '0.75rem', marginBottom: '10px' }}>ECR 审批流转控制:</div>
                <div style={{ display: 'flex', gap: '10px' }}>
                  {selectedChange.approval_status !== 'Approved' && selectedChange.approval_status !== 'Implemented' && (
                    <button className="btn-primary" onClick={() => handleApprove(selectedChange.id)}>
                      <CheckCircle2 size={16} /> 批准变更 (Approve)
                    </button>
                  )}
                  {selectedChange.approval_status === 'Approved' && (
                    <button className="btn-primary" style={{ background: 'linear-gradient(135deg, #10b981, #059669)' }} onClick={() => handleImplement(selectedChange.id)}>
                      <GitPullRequest size={16} /> 执行下发 (Implement & Bump Part Rev)
                    </button>
                  )}
                  {selectedChange.approval_status === 'Implemented' && (
                    <div style={{ color: '#34d399', display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 600 }}>
                      <CheckCircle2 size={16} /> 变更已全面下发生效，零件版本已自动切换至 {selectedChange.post_change_rev}
                    </div>
                  )}
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '16px' }}>
              <button className="btn-secondary" onClick={() => setSelectedChange(null)}>
                关闭窗口
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
