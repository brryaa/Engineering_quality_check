import React, { useEffect, useState } from 'react';
import { api } from '../api/client';
import { Part, Program } from '../types';
import { Badge } from '../components/Badge';
import { Plus, Search, ShieldCheck, AlertCircle } from 'lucide-react';

interface PartsViewProps {
  selectedProgramId?: number;
  programs: Program[];
}

export const PartsView: React.FC<PartsViewProps> = ({ selectedProgramId, programs }) => {
  const [parts, setParts] = useState<Part[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [search, setSearch] = useState<string>('');
  const [subsystemFilter, setSubsystemFilter] = useState<string>('');
  const [page, setPage] = useState<number>(1);
  const [showModal, setShowModal] = useState<boolean>(false);

  // New Part form state
  const [programId, setProgramId] = useState<number>(selectedProgramId || (programs[0]?.id || 1));
  const [partNumber, setPartNumber] = useState('');
  const [name, setName] = useState('');
  const [subsystem, setSubsystem] = useState('Front Door Closure');
  const [category, setCategory] = useState('Mechanical');
  const [supplier, setSupplier] = useState('Brose Group');
  const [material, setMaterial] = useState('EPDM Dense + Sponge 45 Shore A');
  const [revision, setRevision] = useState('Rev A.0');
  const [weightKg, setWeightKg] = useState(1.5);
  const [safetyCritical, setSafetyCritical] = useState(false);

  const loadData = () => {
    setLoading(true);
    api.getParts({
      page,
      page_size: 20,
      search,
      program_id: selectedProgramId,
      subsystem: subsystemFilter || undefined
    })
      .then((res) => {
        setParts(res.items);
        setTotal(res.total);
      })
      .catch((err) => alert(`加载零部件失败: ${err.message}`))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadData();
  }, [page, search, subsystemFilter, selectedProgramId]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createPart({
        program_id: programId,
        part_number: partNumber,
        name,
        subsystem,
        category,
        supplier,
        material,
        revision,
        weight_kg: Number(weightKg),
        safety_critical: safetyCritical
      });
      setShowModal(false);
      setPartNumber('');
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
            零部件与车身开闭件子系统目录 ({total} 件)
          </h1>
          <p style={{ fontSize: '0.85rem', color: '#94a3b8' }}>
            覆盖车门钣金铰链、无框玻璃升降、电动尾门撑杆锁止与高压密封气密条
          </p>
        </div>
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
          <div style={{ position: 'relative' }}>
            <Search size={16} style={{ position: 'absolute', left: '10px', top: '10px', color: '#64748b' }} />
            <input
              type="text"
              placeholder="搜索件号/名称/供应商..."
              className="input-field"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{ paddingLeft: '32px', width: '220px' }}
            />
          </div>

          <select
            className="input-field"
            value={subsystemFilter}
            onChange={(e) => setSubsystemFilter(e.target.value)}
          >
            <option value="">全部工程子系统</option>
            <option value="Front Door Closure">前门开闭机构 Front Door</option>
            <option value="Rear Door Closure">后门开闭机构 Rear Door</option>
            <option value="Power Tailgate System">电动尾门系统 Power Tailgate</option>
            <option value="Frameless Window System">无框车窗导向 Frameless Window</option>
            <option value="Primary Body Seal">车身主密封条 Primary Seal</option>
            <option value="Secondary Acoustic Weatherstrip">副密封降噪条 Acoustic Seal</option>
            <option value="Door Hinge & Check Link">车门铰链限位器 Hinge & Link</option>
            <option value="Glass Regulator Module">玻璃升降电机模块 Regulator</option>
          </select>

          <button className="btn-primary" onClick={() => setShowModal(true)}>
            <Plus size={16} /> 录入新零件
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="glass-panel" style={{ padding: '4px' }}>
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>零件编号 (Part No.)</th>
                <th>零件名称</th>
                <th>工程子系统</th>
                <th>车型归属</th>
                <th>供应商 (Supplier)</th>
                <th>材料规格</th>
                <th>版本 (Rev)</th>
                <th>重量 (kg)</th>
                <th>安全法规件</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={9} style={{ textAlign: 'center', padding: '30px', color: '#94a3b8' }}>
                    正在检索零部件列表...
                  </td>
                </tr>
              ) : parts.length === 0 ? (
                <tr>
                  <td colSpan={9} style={{ textAlign: 'center', padding: '30px', color: '#94a3b8' }}>
                    无符合条件的零部件记录
                  </td>
                </tr>
              ) : (
                parts.map((pt) => (
                  <tr key={pt.id}>
                    <td style={{ fontFamily: 'monospace', fontWeight: 600, color: '#38bdf8' }}>
                      {pt.part_number}
                    </td>
                    <td style={{ fontWeight: 500 }}>{pt.name}</td>
                    <td>{pt.subsystem}</td>
                    <td><Badge label={pt.program_code || 'Global'} variant="indigo" /></td>
                    <td>{pt.supplier}</td>
                    <td style={{ fontSize: '0.8rem', color: '#cbd5e1' }}>{pt.material}</td>
                    <td><Badge label={pt.revision} variant="slate" /></td>
                    <td>{pt.weight_kg} kg</td>
                    <td>
                      {pt.safety_critical ? (
                        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', color: '#f43f5e', fontSize: '0.75rem', fontWeight: 600 }}>
                          <AlertCircle size={14} /> 安全关键件
                        </span>
                      ) : (
                        <span style={{ color: '#64748b', fontSize: '0.75rem' }}>常规件</span>
                      )}
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
              disabled={parts.length < 20}
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
              录入新研发零部件
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
                  <label style={{ fontSize: '0.8rem', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>零件编号 *</label>
                  <input
                    type="text"
                    required
                    placeholder="如: DR-FR-SEAL-01"
                    className="input-field"
                    value={partNumber}
                    onChange={(e) => setPartNumber(e.target.value)}
                    style={{ width: '100%' }}
                  />
                </div>
              </div>

              <div>
                <label style={{ fontSize: '0.8rem', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>零件名称 *</label>
                <input
                  type="text"
                  required
                  placeholder="如: 前门主密封条总成"
                  className="input-field"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  style={{ width: '100%' }}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <label style={{ fontSize: '0.8rem', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>工程子系统</label>
                  <select
                    className="input-field"
                    value={subsystem}
                    onChange={(e) => setSubsystem(e.target.value)}
                    style={{ width: '100%' }}
                  >
                    <option value="Front Door Closure">Front Door Closure</option>
                    <option value="Rear Door Closure">Rear Door Closure</option>
                    <option value="Power Tailgate System">Power Tailgate System</option>
                    <option value="Frameless Window System">Frameless Window System</option>
                    <option value="Primary Body Seal">Primary Body Seal</option>
                    <option value="Secondary Acoustic Weatherstrip">Secondary Acoustic Weatherstrip</option>
                    <option value="Door Hinge & Check Link">Door Hinge & Check Link</option>
                    <option value="Glass Regulator Module">Glass Regulator Module</option>
                  </select>
                </div>
                <div>
                  <label style={{ fontSize: '0.8rem', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>分类 (Category)</label>
                  <select
                    className="input-field"
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    style={{ width: '100%' }}
                  >
                    <option value="Mechanical">Mechanical 机械件</option>
                    <option value="Elastomer / Sealing">Elastomer 弹性体密封</option>
                    <option value="Electro-Mechanical">Electro-Mechanical 机电一体</option>
                    <option value="Glass & Guiding">Glass 玻璃导向</option>
                    <option value="Structural / Hinge">Structural 结构铰链</option>
                  </select>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <label style={{ fontSize: '0.8rem', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>供应商</label>
                  <input
                    type="text"
                    className="input-field"
                    value={supplier}
                    onChange={(e) => setSupplier(e.target.value)}
                    style={{ width: '100%' }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '0.8rem', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>材料牌号</label>
                  <input
                    type="text"
                    className="input-field"
                    value={material}
                    onChange={(e) => setMaterial(e.target.value)}
                    style={{ width: '100%' }}
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '12px' }}>
                <div>
                  <label style={{ fontSize: '0.8rem', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>版本号</label>
                  <input
                    type="text"
                    className="input-field"
                    value={revision}
                    onChange={(e) => setRevision(e.target.value)}
                    style={{ width: '100%' }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '0.8rem', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>重量 (kg)</label>
                  <input
                    type="number"
                    step="0.01"
                    className="input-field"
                    value={weightKg}
                    onChange={(e) => setWeightKg(Number(e.target.value))}
                    style={{ width: '100%' }}
                  />
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.85rem', color: '#f8fafc', cursor: 'pointer', marginTop: '16px' }}>
                    <input
                      type="checkbox"
                      checked={safetyCritical}
                      onChange={(e) => setSafetyCritical(e.target.checked)}
                    />
                    安全关键件
                  </label>
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '10px' }}>
                <button type="button" className="btn-secondary" onClick={() => setShowModal(false)}>
                  取消
                </button>
                <button type="submit" className="btn-primary">
                  保存并入库
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
