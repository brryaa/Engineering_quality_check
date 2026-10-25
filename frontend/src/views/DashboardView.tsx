import React, { useEffect, useState } from 'react';
import { api } from '../api/client';
import { QualityDashboardStats } from '../types';
import { Badge } from '../components/Badge';
import {
  Car, Layers, AlertTriangle, FileCheck, FlaskConical,
  AlertCircle, GitPullRequest, TrendingUp, ShieldAlert, CheckCircle2
} from 'lucide-react';

interface DashboardViewProps {
  selectedProgramId?: number;
}

export const DashboardView: React.FC<DashboardViewProps> = ({ selectedProgramId }) => {
  const [stats, setStats] = useState<QualityDashboardStats | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    api.getDashboardStats(selectedProgramId)
      .then((data) => {
        setStats(data);
        setError(null);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [selectedProgramId]);

  if (loading) {
    return (
      <div style={{ padding: '40px', textAlign: 'center', color: '#94a3b8' }}>
        正在加载研发质量全景数据...
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div style={{ padding: '40px', textAlign: 'center', color: '#f43f5e' }}>
        数据加载失败: {error || '未知错误'}
      </div>
    );
  }

  return (
    <div style={{ padding: '24px', maxWidth: '1440px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Top Banner / Program indicator */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        background: 'linear-gradient(90deg, #1e293b, #0f172a)',
        padding: '16px 24px',
        borderRadius: '12px',
        border: '1px solid rgba(255, 255, 255, 0.08)'
      }}>
        <div>
          <h1 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#f8fafc' }}>
            质量工程总览仪表盘 {selectedProgramId ? `(车型项目 #${selectedProgramId})` : '(全局统计)'}
          </h1>
          <p style={{ fontSize: '0.875rem', color: '#94a3b8' }}>
            AIAG-VDA 风险控制 · DVP&R 试验闭环 · 8D / 5-Why 根因归零 · ECR 变更成本
          </p>
        </div>
        <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>综合试验合格率</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 800, color: stats.test_run_pass_rate_pct >= 80 ? '#34d399' : '#fbbf24' }}>
              {stats.test_run_pass_rate_pct}%
            </div>
          </div>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>待闭环S1致命问题</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 800, color: stats.open_critical_issues_count > 0 ? '#f43f5e' : '#34d399' }}>
              {stats.open_critical_issues_count}
            </div>
          </div>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
        gap: '16px'
      }}>
        <div className="glass-panel" style={{ padding: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: '#94a3b8', fontSize: '0.85rem' }}>
            <span>车型项目</span>
            <Car size={18} color="#38bdf8" />
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 700, marginTop: '8px', color: '#f8fafc' }}>
            {stats.total_programs}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '4px' }}>平台与衍生车型</div>
        </div>

        <div className="glass-panel" style={{ padding: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: '#94a3b8', fontSize: '0.85rem' }}>
            <span>在控零部件</span>
            <Layers size={18} color="#818cf8" />
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 700, marginTop: '8px', color: '#f8fafc' }}>
            {stats.total_parts}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '4px' }}>车身开闭件与密封</div>
        </div>

        <div className="glass-panel" style={{ padding: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: '#94a3b8', fontSize: '0.85rem' }}>
            <span>DFMEA分析项</span>
            <AlertTriangle size={18} color="#fbbf24" />
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 700, marginTop: '8px', color: '#f8fafc' }}>
            {stats.total_dfmeas}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#fbbf24', marginTop: '4px' }}>
            高风险(High AP): {stats.dfmea_high_ap_count} 条
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: '#94a3b8', fontSize: '0.85rem' }}>
            <span>DVP&R验证项</span>
            <FileCheck size={18} color="#34d399" />
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 700, marginTop: '8px', color: '#f8fafc' }}>
            {stats.total_dvprs}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '4px' }}>包含DV/PV全阶段</div>
        </div>

        <div className="glass-panel" style={{ padding: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: '#94a3b8', fontSize: '0.85rem' }}>
            <span>试验执行记录</span>
            <FlaskConical size={18} color="#c084fc" />
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 700, marginTop: '8px', color: '#f8fafc' }}>
            {stats.total_test_runs}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#34d399', marginTop: '4px' }}>
            通过: {stats.test_run_result_counts['Pass'] || 0} | 失败: {stats.test_run_result_counts['Fail'] || 0}
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: '#94a3b8', fontSize: '0.85rem' }}>
            <span>工程问题总数</span>
            <AlertCircle size={18} color="#f43f5e" />
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 700, marginTop: '8px', color: '#f8fafc' }}>
            {stats.total_issues}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '4px' }}>PRTS / 8D闭环流程</div>
        </div>

        <div className="glass-panel" style={{ padding: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: '#94a3b8', fontSize: '0.85rem' }}>
            <span>工程变更(ECR)</span>
            <GitPullRequest size={18} color="#38bdf8" />
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 700, marginTop: '8px', color: '#f8fafc' }}>
            {stats.total_changes}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '4px' }}>
            净成本影响: ¥{stats.total_change_cost_impact_rmb.toLocaleString()}
          </div>
        </div>
      </div>

      {/* Middle Grid: DFMEA AP Pareto + DVP&R Burndown + Issue Severity */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '20px' }}>
        {/* DFMEA Action Priority (AIAG & VDA 2019) */}
        <div className="glass-panel" style={{ padding: '20px' }}>
          <h2 style={{ fontSize: '1rem', fontWeight: 600, color: '#f8fafc', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <ShieldAlert size={18} color="#fbbf24" />
            DFMEA 风险行动优先级 (AIAG-VDA AP)
          </h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '4px' }}>
                <span style={{ color: '#fb7185' }}>高优先级 High AP (必须整改)</span>
                <span style={{ fontWeight: 600 }}>{stats.dfmea_high_ap_count} 条</span>
              </div>
              <div style={{ height: '8px', background: '#334155', borderRadius: '4px', overflow: 'hidden' }}>
                <div style={{
                  height: '100%',
                  width: `${(stats.dfmea_high_ap_count / (stats.total_dfmeas || 1)) * 100}%`,
                  background: '#f43f5e'
                }} />
              </div>
            </div>

            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '4px' }}>
                <span style={{ color: '#fbbf24' }}>中优先级 Medium AP (建议预防)</span>
                <span style={{ fontWeight: 600 }}>{stats.dfmea_medium_ap_count} 条</span>
              </div>
              <div style={{ height: '8px', background: '#334155', borderRadius: '4px', overflow: 'hidden' }}>
                <div style={{
                  height: '100%',
                  width: `${(stats.dfmea_medium_ap_count / (stats.total_dfmeas || 1)) * 100}%`,
                  background: '#f59e0b'
                }} />
              </div>
            </div>

            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '4px' }}>
                <span style={{ color: '#34d399' }}>低优先级 Low AP (常规监控)</span>
                <span style={{ fontWeight: 600 }}>{stats.dfmea_low_ap_count} 条</span>
              </div>
              <div style={{ height: '8px', background: '#334155', borderRadius: '4px', overflow: 'hidden' }}>
                <div style={{
                  height: '100%',
                  width: `${(stats.dfmea_low_ap_count / (stats.total_dfmeas || 1)) * 100}%`,
                  background: '#10b981'
                }} />
              </div>
            </div>

            <div style={{ marginTop: '12px', padding: '10px', background: '#0f172a', borderRadius: '6px', fontSize: '0.8rem', color: '#94a3b8' }}>
              💡 传统 RPN ≥ 100 警戒项共计 <strong style={{ color: '#f8fafc' }}>{stats.dfmea_high_rpn_count}</strong> 项，均已强制触发预防/探测控制措施。
            </div>
          </div>
        </div>

        {/* DVP&R Verification Burndown */}
        <div className="glass-panel" style={{ padding: '20px' }}>
          <h2 style={{ fontSize: '1rem', fontWeight: 600, color: '#f8fafc', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <FileCheck size={18} color="#34d399" />
            DVP&R 验证进度燃尽状态
          </h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px' }}>
            {Object.entries(stats.dvpr_status_counts).map(([st, cnt]) => (
              <div key={st} style={{ background: '#0f172a', padding: '12px', borderRadius: '8px', border: '1px solid #334155' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '0.85rem', color: '#94a3b8' }}>{st}</span>
                  <Badge label={st} />
                </div>
                <div style={{ fontSize: '1.25rem', fontWeight: 700, marginTop: '6px', color: '#f8fafc' }}>
                  {cnt}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Issue Severity Distribution */}
        <div className="glass-panel" style={{ padding: '20px' }}>
          <h2 style={{ fontSize: '1rem', fontWeight: 600, color: '#f8fafc', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <AlertCircle size={18} color="#f43f5e" />
            问题严重度 (Severity) 分级
          </h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {Object.entries(stats.issue_severity_counts).map(([sev, cnt]) => (
              <div key={sev} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 12px', background: '#0f172a', borderRadius: '6px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Badge label={sev} />
                  <span style={{ fontSize: '0.85rem', color: '#cbd5e1' }}>{sev}</span>
                </div>
                <span style={{ fontWeight: 700, color: '#f8fafc' }}>{cnt} 件</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Subsystem Health Ranking */}
      <div className="glass-panel" style={{ padding: '20px' }}>
        <h2 style={{ fontSize: '1rem', fontWeight: 600, color: '#f8fafc', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <TrendingUp size={18} color="#38bdf8" />
          开闭件与密封子系统健康度排名 (Subsystem Health Index)
        </h2>
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>子系统名称</th>
                <th>关联问题总数</th>
                <th>未闭环 S1 致命缺陷</th>
                <th>质量健康分 (0-100)</th>
                <th>质量状态</th>
              </tr>
            </thead>
            <tbody>
              {stats.subsystem_health.map((sh) => (
                <tr key={sh.subsystem}>
                  <td style={{ fontWeight: 600, color: '#38bdf8' }}>{sh.subsystem}</td>
                  <td>{sh.total_issues} 件</td>
                  <td style={{ color: sh.open_critical_issues > 0 ? '#f43f5e' : '#34d399', fontWeight: 600 }}>
                    {sh.open_critical_issues}
                  </td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <div style={{ width: '80px', height: '6px', background: '#334155', borderRadius: '3px', overflow: 'hidden' }}>
                        <div style={{
                          height: '100%',
                          width: `${sh.health_score}%`,
                          background: sh.health_score > 75 ? '#10b981' : sh.health_score > 50 ? '#f59e0b' : '#f43f5e'
                        }} />
                      </div>
                      <span style={{ fontWeight: 700 }}>{sh.health_score}</span>
                    </div>
                  </td>
                  <td>
                    {sh.health_score >= 80 ? (
                      <Badge label="受控 Normal" variant="emerald" />
                    ) : sh.health_score >= 60 ? (
                      <Badge label="预警 Attention" variant="amber" />
                    ) : (
                      <Badge label="高风险 Critical" variant="rose" />
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
