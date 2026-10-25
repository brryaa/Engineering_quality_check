import React, { useEffect, useState } from 'react';
import { api } from '../api/client';
import { TestRun } from '../types';
import { Badge } from '../components/Badge';
import { Search, FlaskConical, Thermometer, Activity, Eye } from 'lucide-react';

export const TestRunsView: React.FC = () => {
  const [testRuns, setTestRuns] = useState<TestRun[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [search, setSearch] = useState<string>('');
  const [resultFilter, setResultFilter] = useState<string>('');
  const [page, setPage] = useState<number>(1);
  const [selectedRun, setSelectedRun] = useState<TestRun | null>(null);

  const loadData = () => {
    setLoading(true);
    api.getTestRuns({
      page,
      page_size: 20,
      search,
      result: resultFilter || undefined
    })
      .then((res) => {
        setTestRuns(res.items);
        setTotal(res.total);
      })
      .catch((err) => alert(`加载试验记录失败: ${err.message}`))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadData();
  }, [page, search, resultFilter]);

  const parseTelemetry = (raw: string) => {
    try {
      return JSON.parse(raw);
    } catch {
      return {};
    }
  };

  return (
    <div style={{ padding: '24px', maxWidth: '1440px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Header & Controls */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h1 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#f8fafc' }}>
            试验执行与台架遥测记录 ({total} 轮次)
          </h1>
          <p style={{ fontSize: '0.85rem', color: '#94a3b8' }}>
            开闭件撞击耐久、温湿度交变 (-40℃ ~ 85℃)、淋雨密封性与车窗防夹力实测数据
          </p>
        </div>
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
          <div style={{ position: 'relative' }}>
            <Search size={16} style={{ position: 'absolute', left: '10px', top: '10px', color: '#64748b' }} />
            <input
              type="text"
              placeholder="搜索试验单号/样件/试验员..."
              className="input-field"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{ paddingLeft: '32px', width: '220px' }}
            />
          </div>

          <select
            className="input-field"
            value={resultFilter}
            onChange={(e) => setResultFilter(e.target.value)}
          >
            <option value="">全部试验结果</option>
            <option value="Pass">🟢 合格 Pass</option>
            <option value="Fail">🔴 失败 Fail</option>
            <option value="Marginal">🟡 临界 Marginal</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="glass-panel" style={{ padding: '4px' }}>
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>试验单号 (Run No.)</th>
                <th>关联 DVP 计划</th>
                <th>试验样件号</th>
                <th>试验日期</th>
                <th>试验设施与环境</th>
                <th>完成循环次数</th>
                <th>关键遥测实测值 (Telemetry)</th>
                <th>判定结果</th>
                <th>试验员</th>
                <th>遥测报表</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={10} style={{ textAlign: 'center', padding: '30px', color: '#94a3b8' }}>
                    正在检索试验数据流...
                  </td>
                </tr>
              ) : testRuns.length === 0 ? (
                <tr>
                  <td colSpan={10} style={{ textAlign: 'center', padding: '30px', color: '#94a3b8' }}>
                    无符合条件的试验记录
                  </td>
                </tr>
              ) : (
                testRuns.map((tr) => {
                  const telemetry = parseTelemetry(tr.measurement_data);
                  return (
                    <tr key={tr.id}>
                      <td style={{ fontFamily: 'monospace', fontWeight: 600, color: '#38bdf8' }}>
                        {tr.run_number}
                      </td>
                      <td style={{ fontSize: '0.8rem', maxWidth: '200px' }}>
                        <div style={{ color: '#38bdf8', fontWeight: 600 }}>{tr.plan_code}</div>
                        <div style={{ color: '#94a3b8', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {tr.test_name}
                        </div>
                      </td>
                      <td style={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>{tr.sample_id}</td>
                      <td style={{ fontSize: '0.8rem' }}>{tr.test_date}</td>
                      <td style={{ fontSize: '0.8rem' }}>
                        <div>{tr.test_facility}</div>
                        <div style={{ color: tr.temperature_c <= 0 ? '#38bdf8' : tr.temperature_c >= 50 ? '#f43f5e' : '#94a3b8', fontSize: '0.75rem' }}>
                          {tr.temperature_c}℃ · {tr.humidity_rh}% RH
                        </div>
                      </td>
                      <td style={{ fontWeight: 600, textAlign: 'center' }}>
                        {tr.cycles_completed.toLocaleString()} 次
                      </td>
                      <td style={{ fontSize: '0.75rem', maxWidth: '240px' }}>
                        {telemetry.residual_sag_mm !== undefined && (
                          <div>下垂量: <strong style={{ color: telemetry.residual_sag_mm > 1.5 ? '#f43f5e' : '#34d399' }}>{telemetry.residual_sag_mm} mm</strong></div>
                        )}
                        {telemetry.pinch_force_n !== undefined && (
                          <div>防夹力: <strong style={{ color: telemetry.pinch_force_n > 100 ? '#f43f5e' : '#34d399' }}>{telemetry.pinch_force_n} N</strong></div>
                        )}
                        {telemetry.water_leak_ml_min !== undefined && (
                          <div>漏水量: <strong style={{ color: telemetry.water_leak_ml_min > 0 ? '#f43f5e' : '#34d399' }}>{telemetry.water_leak_ml_min} ml/min</strong></div>
                        )}
                      </td>
                      <td>
                        <Badge label={tr.result} />
                      </td>
                      <td style={{ fontSize: '0.8rem' }}>{tr.operator}</td>
                      <td>
                        <button
                          className="btn-secondary"
                          style={{ padding: '4px 8px', fontSize: '0.75rem' }}
                          onClick={() => setSelectedRun(tr)}
                        >
                          <Eye size={12} /> 详情
                        </button>
                      </td>
                    </tr>
                  );
                })
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
              disabled={testRuns.length < 20}
              onClick={() => setPage((p) => p + 1)}
            >
              下一页
            </button>
          </div>
        </div>
      </div>

      {/* Telemetry Detail Modal */}
      {selectedRun && (
        <div className="modal-overlay">
          <div className="modal-content" style={{ padding: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div>
                <span style={{ fontSize: '0.8rem', color: '#38bdf8', fontWeight: 600 }}>{selectedRun.run_number}</span>
                <h2 style={{ fontSize: '1.15rem', fontWeight: 700, color: '#f8fafc' }}>
                  试验执行数据详情
                </h2>
              </div>
              <Badge label={selectedRun.result} />
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', fontSize: '0.85rem' }}>
              <div style={{ background: '#0f172a', padding: '12px', borderRadius: '8px' }}>
                <div style={{ color: '#94a3b8', fontSize: '0.75rem' }}>关联 DVP 验证项</div>
                <div style={{ fontWeight: 600, color: '#f8fafc', marginTop: '2px' }}>{selectedRun.test_name}</div>
                <div style={{ color: '#38bdf8', fontSize: '0.8rem' }}>{selectedRun.plan_code}</div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px' }}>
                <div style={{ background: '#0f172a', padding: '10px', borderRadius: '6px' }}>
                  <div style={{ color: '#94a3b8', fontSize: '0.7rem' }}>环境温度</div>
                  <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc' }}>{selectedRun.temperature_c} ℃</div>
                </div>
                <div style={{ background: '#0f172a', padding: '10px', borderRadius: '6px' }}>
                  <div style={{ color: '#94a3b8', fontSize: '0.7rem' }}>相对湿度</div>
                  <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc' }}>{selectedRun.humidity_rh} % RH</div>
                </div>
                <div style={{ background: '#0f172a', padding: '10px', borderRadius: '6px' }}>
                  <div style={{ color: '#94a3b8', fontSize: '0.7rem' }}>循环圈数</div>
                  <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc' }}>{selectedRun.cycles_completed}</div>
                </div>
              </div>

              <div style={{ background: '#0f172a', padding: '12px', borderRadius: '8px' }}>
                <div style={{ color: '#38bdf8', fontSize: '0.75rem', marginBottom: '8px' }}>台架传感器实测原始数据 (JSON Telemetry)</div>
                <pre style={{
                  background: '#090d16',
                  padding: '10px',
                  borderRadius: '6px',
                  fontSize: '0.75rem',
                  color: '#34d399',
                  overflowX: 'auto',
                  fontFamily: 'monospace'
                }}>
                  {JSON.stringify(parseTelemetry(selectedRun.measurement_data), null, 2)}
                </pre>
              </div>

              {selectedRun.failure_summary && (
                <div style={{ background: 'rgba(244, 63, 94, 0.1)', border: '1px solid rgba(244, 63, 94, 0.3)', padding: '12px', borderRadius: '8px' }}>
                  <div style={{ color: '#fb7185', fontWeight: 600, marginBottom: '4px' }}>失效现象诊断描述:</div>
                  <div style={{ color: '#fecdd3' }}>{selectedRun.failure_summary}</div>
                </div>
              )}
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '16px' }}>
              <button className="btn-secondary" onClick={() => setSelectedRun(null)}>
                关闭
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
