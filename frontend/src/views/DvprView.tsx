import React, { useEffect, useState } from 'react';
import { api } from '../api/client';
import { DVPR, Program, Part } from '../types';
import { Badge } from '../components/Badge';
import { Plus, Search, FileCheck, CheckCircle2 } from 'lucide-react';

interface DvprViewProps {
  selectedProgramId?: number;
  programs: Program[];
}

export const DvprView: React.FC<DvprViewProps> = ({ selectedProgramId, programs }) => {
  const [dvprs, setDvprs] = useState<DVPR[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [search, setSearch] = useState<string>('');
  const [phaseFilter, setPhaseFilter] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [page, setPage] = useState<number>(1);
  const [showModal, setShowModal] = useState<boolean>(false);

  // New DVP form state
  const [programId, setProgramId] = useState<number>(selectedProgramId || (programs[0]?.id || 1));
  const [partId, setPartId] = useState<number>(1);
  const [planCode, setPlanCode] = useState('');
  const [testPhase, setTestPhase] = useState('DV-A');
  const [testName, setTestName] = useState('Side Door Slam Durability 100,000 Cycles');
  const [testStandard, setTestStandard] = useState('QC/T 627-2022');
  const [acceptanceCriteria, setAcceptanceCriteria] = useState('Door sag <= 1.5mm, latch functional');
  const [sampleSize, setSampleSize] = useState(3);
  const [testFacility, setTestFacility] = useState('Closure Durability Rig #1');
  const [plannedStartDate, setPlannedStartDate] = useState('2026-11-01');
  const [plannedEndDate, setPlannedEndDate] = useState('2026-11-20');
  const [responsibleEngineer, setResponsibleEngineer] = useState('Dr. Wei Chen');

  const loadData = () => {
    setLoading(true);
    api.getDvprs({
      page,
      page_size: 20,
      search,
      program_id: selectedProgramId,
      test_phase: phaseFilter || undefined,
      status: statusFilter || undefined
    })
      .then((res) => {
        setDvprs(res.items);
        setTotal(res.total);
      })
      .catch((err) => alert(`加载DVP&R计划失败: ${err.message}`))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadData();
  }, [page, search, phaseFilter, statusFilter, selectedProgramId]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createDvpr({
        program_id: programId,
        part_id: partId,
        plan_code: planCode,
        test_phase: testPhase,
        test_name: testName,
        test_standard: testStandard,
        acceptance_criteria: acceptanceCriteria,
        sample_size: Number(sampleSize),
        test_facility: testFacility,
        planned_start_date: plannedStartDate,
        planned_end_date: plannedEndDate,
        status: 'Planned',
        responsible_engineer: responsibleEngineer
      });
      setShowModal(false);
      setPlanCode('');
      loadData();
    } catch (err: any) {
      alert(`创建失败: ${err.message}`);
    }
  };

  return (
    <div style={{ padding: '24px', maxWidth: '1440px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Header & Controls */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h1 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#f8fafc' }}>
            DVP&R 设计验证试验计划与报告 ({total} 项)
          </h1>
          <p style={{ fontSize: '0.85rem', color: '#94a3b8' }}>
            覆盖整车 DV-A / DV-B 样车验证及 PV 生产确认试验标准与验收准则
          </p>
        </div>
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
          <div style={{ position: 'relative' }}>
            <Search size={16} style={{ position: 'absolute', left: '10px', top: '10px', color: '#64748b' }} />
            <input
              type="text"
              placeholder="搜索验证计划/试验标准/项目..."
              className="input-field"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{ paddingLeft: '32px', width: '220px' }}
            />
          </div>

          <select
            className="input-field"
            value={phaseFilter}
            onChange={(e) => setPhaseFilter(e.target.value)}
          >
            <option value="">全部验证阶段</option>
            <option value="DV-A">DV-A 阶段试验</option>
            <option value="DV-B">DV-B 阶段试验</option>
            <option value="PV-C">PV-C 试生产试验</option>
            <option value="SOP-Confirm">SOP-Confirm 量产确认</option>
          </select>

          <select
            className="input-field"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="">全部计划状态</option>
            <option value="Planned">计划中 Planned</option>
            <option value="In Progress">进行中 In Progress</option>
            <option value="Passed">已通过 Passed</option>
            <option value="Failed">未通过 Failed</option>
            <option value="Blocked">阻塞 Blocked</option>
          </select>

          <button className="btn-primary" onClick={() => setShowModal(true)}>
            <Plus size={16} /> 制定验证计划
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="glass-panel" style={{ padding: '4px' }}>
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>计划编号 (Plan Code)</th>
                <th>车型</th>
                <th>关联零件号</th>
                <th>验证阶段</th>
                <th>试验项目与内容</th>
                <th>执行标准 (Standard)</th>
                <th>合格判定依据 (Acceptance Criteria)</th>
                <th>样本量</th>
                <th>试验设施/台架</th>
                <th>状态</th>
                <th>已执行轮次</th>
                <th>责任工程师</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={12} style={{ textAlign: 'center', padding: '30px', color: '#94a3b8' }}>
                    正在检索 DVP&R 计划...
                  </td>
                </tr>
              ) : dvprs.length === 0 ? (
                <tr>
                  <td colSpan={12} style={{ textAlign: 'center', padding: '30px', color: '#94a3b8' }}>
                    无符合条件的验证计划
                  </td>
                </tr>
              ) : (
                dvprs.map((dv) => (
                  <tr key={dv.id}>
                    <td style={{ fontFamily: 'monospace', fontWeight: 600, color: '#38bdf8' }}>
                      {dv.plan_code}
                    </td>
                    <td><Badge label={dv.program_code || 'Global'} variant="indigo" /></td>
                    <td style={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>{dv.part_number}</td>
                    <td><Badge label={dv.test_phase} variant="slate" /></td>
                    <td style={{ fontWeight: 500, color: '#f8fafc', maxWidth: '240px' }}>
                      {dv.test_name}
                    </td>
                    <td style={{ color: '#38bdf8', fontWeight: 600, fontSize: '0.8rem' }}>
                      {dv.test_standard}
                    </td>
                    <td style={{ fontSize: '0.8rem', color: '#cbd5e1', maxWidth: '220px' }}>
                      {dv.acceptance_criteria}
                    </td>
                    <td style={{ textAlign: 'center' }}>{dv.sample_size} pcs</td>
                    <td style={{ fontSize: '0.8rem', color: '#94a3b8' }}>{dv.test_facility}</td>
                    <td><Badge label={dv.status} /></td>
                    <td style={{ textAlign: 'center', fontWeight: 700, color: dv.test_runs_count ? '#34d399' : '#94a3b8' }}>
                      {dv.test_runs_count || 0}
                    </td>
                    <td>{dv.responsible_engineer}</td>
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
              disabled={dvprs.length < 20}
              onClick={() => setPage((p) => p + 1)}
            >
              下一页
            </button>
          </div>
        </div>
      </div>

      {/* Create Modal */}
      {showModal && (
        <div className="modal-overlay">
          <div className="modal-content" style={{ padding: '24px' }}>
            <h2 style={{ fontSize: '1.15rem', fontWeight: 600, color: '#f8fafc', marginBottom: '16px' }}>
              制定新 DVP&R 试验验证计划
            </h2>
            <form onSubmit={handleCreate} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <label style={{ fontSize: '0.8rem', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>车型项目 *</label>
                  <select
                    className="input-field"
                    value={programId}
                    onChange={(e) => setProgramId(Number(e.target.value))}
                    style={{ width: '100%' }}
                  >
                    {programs.map((p) => (
                      <option key={p.id} value={p.id}>{p.code} - {p.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label style={{ fontSize: '0.8rem', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>验证计划编号 *</label>
                  <input
                    type="text"
                    required
                    placeholder="如: DVP-2026-SLAM01"
                    className="input-field"
                    value={planCode}
                    onChange={(e) => setPlanCode(e.target.value)}
                    style={{ width: '100%' }}
                  />
                </div>
              </div>

              <div>
                <label style={{ fontSize: '0.8rem', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>试验项目名称 *</label>
                <input
                  type="text"
                  required
                  className="input-field"
                  value={testName}
                  onChange={(e) => setTestName(e.target.value)}
                  style={{ width: '100%' }}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <label style={{ fontSize: '0.8rem', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>验证阶段</label>
                  <select
                    className="input-field"
                    value={testPhase}
                    onChange={(e) => setTestPhase(e.target.value)}
                    style={{ width: '100%' }}
                  >
                    <option value="DV-A">DV-A 设计验证</option>
                    <option value="DV-B">DV-B 深度验证</option>
                    <option value="PV-C">PV-C 生产确认</option>
                    <option value="SOP-Confirm">SOP-Confirm 量产确认</option>
                  </select>
                </div>
                <div>
                  <label style={{ fontSize: '0.8rem', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>执行标准</label>
                  <input
                    type="text"
                    required
                    className="input-field"
                    value={testStandard}
                    onChange={(e) => setTestStandard(e.target.value)}
                    style={{ width: '100%' }}
                  />
                </div>
              </div>

              <div>
                <label style={{ fontSize: '0.8rem', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>合格验收判据 *</label>
                <textarea
                  required
                  rows={2}
                  className="input-field"
                  value={acceptanceCriteria}
                  onChange={(e) => setAcceptanceCriteria(e.target.value)}
                  style={{ width: '100%', resize: 'vertical' }}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '12px' }}>
                <div>
                  <label style={{ fontSize: '0.8rem', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>样本数量 (pcs)</label>
                  <input
                    type="number"
                    min="1"
                    className="input-field"
                    value={sampleSize}
                    onChange={(e) => setSampleSize(Number(e.target.value))}
                    style={{ width: '100%' }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '0.8rem', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>试验台架/环境</label>
                  <input
                    type="text"
                    className="input-field"
                    value={testFacility}
                    onChange={(e) => setTestFacility(e.target.value)}
                    style={{ width: '100%' }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '0.8rem', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>责任工程师</label>
                  <input
                    type="text"
                    className="input-field"
                    value={responsibleEngineer}
                    onChange={(e) => setResponsibleEngineer(e.target.value)}
                    style={{ width: '100%' }}
                  />
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '10px' }}>
                <button type="button" className="btn-secondary" onClick={() => setShowModal(false)}>
                  取消
                </button>
                <button type="submit" className="btn-primary">
                  保存并排期
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
