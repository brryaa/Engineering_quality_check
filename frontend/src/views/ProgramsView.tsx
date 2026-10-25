import React, { useEffect, useState } from 'react';
import { api } from '../api/client';
import { Program } from '../types';
import { Badge } from '../components/Badge';
import { Plus, Search, Car, Calendar, User, Globe } from 'lucide-react';

export const ProgramsView: React.FC = () => {
  const [programs, setPrograms] = useState<Program[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [search, setSearch] = useState<string>('');
  const [phaseFilter, setPhaseFilter] = useState<string>('');
  const [showModal, setShowModal] = useState<boolean>(false);
  
  // New Program form state
  const [code, setCode] = useState('');
  const [name, setName] = useState('');
  const [platform, setPlatform] = useState('EV-800V-Platform');
  const [phase, setPhase] = useState('Proto-A');
  const [sopDate, setSopDate] = useState('2027-10-01');
  const [leadEngineer, setLeadEngineer] = useState('Dr. Wei Chen');
  const [qualityManager, setQualityManager] = useState('Ying Zhao');
  const [targetMarket, setTargetMarket] = useState('Global');
  const [description, setDescription] = useState('');

  const loadData = () => {
    setLoading(true);
    api.getPrograms({ search, phase: phaseFilter || undefined, page_size: 50 })
      .then((res) => setPrograms(res.items))
      .catch((err) => alert(`加载失败: ${err.message}`))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadData();
  }, [search, phaseFilter]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createProgram({
        code, name, platform, phase, sop_date: sopDate,
        lead_engineer: leadEngineer, quality_manager: qualityManager,
        target_market: targetMarket, description
      });
      setShowModal(false);
      setCode('');
      setName('');
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
            车型项目与研发平台管理
          </h1>
          <p style={{ fontSize: '0.85rem', color: '#94a3b8' }}>
            管理汽车整车项目开发阶段、SOP里程碑节点与研发质量责任人
          </p>
        </div>
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <div style={{ position: 'relative' }}>
            <Search size={16} style={{ position: 'absolute', left: '10px', top: '10px', color: '#64748b' }} />
            <input
              type="text"
              placeholder="搜索项目代号/名称..."
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
            <option value="">全部开发阶段</option>
            <option value="Concept">Concept 概念</option>
            <option value="Proto-A">Proto-A 样车A阶段</option>
            <option value="Pre-series-B">Pre-series-B 预批量B阶段</option>
            <option value="PPAP">PPAP 生产件批准</option>
            <option value="SOP">SOP 量产</option>
          </select>
          <button className="btn-primary" onClick={() => setShowModal(true)}>
            <Plus size={16} /> 新建车型项目
          </button>
        </div>
      </div>

      {/* Cards Grid */}
      {loading ? (
        <div style={{ padding: '40px', textAlign: 'center', color: '#94a3b8' }}>正在加载车型数据...</div>
      ) : programs.length === 0 ? (
        <div style={{ padding: '40px', textAlign: 'center', color: '#94a3b8' }}>暂无符合条件的车型项目</div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '16px' }}>
          {programs.map((p) => (
            <div key={p.id} className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#38bdf8', letterSpacing: '0.05em' }}>
                    {p.code}
                  </span>
                  <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: '#f8fafc', marginTop: '2px' }}>
                    {p.name}
                  </h3>
                </div>
                <Badge label={p.phase} />
              </div>

              <div style={{ fontSize: '0.85rem', color: '#cbd5e1', lineHeight: '1.4' }}>
                {p.description || `整车研发项目 ${p.name} 基于 ${p.platform} 架构平台打造。`}
              </div>

              <div style={{ borderTop: '1px solid #334155', paddingTop: '12px', display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '0.8rem', color: '#94a3b8' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Car size={14} color="#38bdf8" />
                  <span>平台架构: <strong style={{ color: '#f8fafc' }}>{p.platform}</strong></span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Calendar size={14} color="#34d399" />
                  <span>SOP量产计划: <strong style={{ color: '#f8fafc' }}>{p.sop_date || '待定'}</strong></span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <User size={14} color="#fbbf24" />
                  <span>负责人: {p.lead_engineer} (总工) · {p.quality_manager} (质量经理)</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Globe size={14} color="#818cf8" />
                  <span>目标市场: {p.target_market}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Modal */}
      {showModal && (
        <div className="modal-overlay">
          <div className="modal-content" style={{ padding: '24px' }}>
            <h2 style={{ fontSize: '1.15rem', fontWeight: 600, color: '#f8fafc', marginBottom: '16px' }}>
              创建新车型工程项目
            </h2>
            <form onSubmit={handleCreate} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <label style={{ fontSize: '0.8rem', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>
                  项目代码 (Code) *
                </label>
                <input
                  type="text"
                  required
                  placeholder="例如: P-EP40"
                  className="input-field"
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  style={{ width: '100%' }}
                />
              </div>

              <div>
                <label style={{ fontSize: '0.8rem', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>
                  车型名称 (Model Name) *
                </label>
                <input
                  type="text"
                  required
                  placeholder="例如: Aurora EV Coupe"
                  className="input-field"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  style={{ width: '100%' }}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <label style={{ fontSize: '0.8rem', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>平台架构</label>
                  <input
                    type="text"
                    required
                    className="input-field"
                    value={platform}
                    onChange={(e) => setPlatform(e.target.value)}
                    style={{ width: '100%' }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '0.8rem', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>开发阶段</label>
                  <select
                    className="input-field"
                    value={phase}
                    onChange={(e) => setPhase(e.target.value)}
                    style={{ width: '100%' }}
                  >
                    <option value="Concept">Concept</option>
                    <option value="Proto-A">Proto-A</option>
                    <option value="Pre-series-B">Pre-series-B</option>
                    <option value="PPAP">PPAP</option>
                    <option value="SOP">SOP</option>
                  </select>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <label style={{ fontSize: '0.8rem', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>计划SOP日期</label>
                  <input
                    type="date"
                    className="input-field"
                    value={sopDate}
                    onChange={(e) => setSopDate(e.target.value)}
                    style={{ width: '100%' }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '0.8rem', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>目标市场</label>
                  <input
                    type="text"
                    className="input-field"
                    value={targetMarket}
                    onChange={(e) => setTargetMarket(e.target.value)}
                    style={{ width: '100%' }}
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <label style={{ fontSize: '0.8rem', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>研发主管工程师</label>
                  <input
                    type="text"
                    className="input-field"
                    value={leadEngineer}
                    onChange={(e) => setLeadEngineer(e.target.value)}
                    style={{ width: '100%' }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '0.8rem', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>质量总监/经理</label>
                  <input
                    type="text"
                    className="input-field"
                    value={qualityManager}
                    onChange={(e) => setQualityManager(e.target.value)}
                    style={{ width: '100%' }}
                  />
                </div>
              </div>

              <div>
                <label style={{ fontSize: '0.8rem', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>项目概述</label>
                <textarea
                  className="input-field"
                  rows={3}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  style={{ width: '100%', resize: 'vertical' }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '10px' }}>
                <button type="button" className="btn-secondary" onClick={() => setShowModal(false)}>
                  取消
                </button>
                <button type="submit" className="btn-primary">
                  保存并提交
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
