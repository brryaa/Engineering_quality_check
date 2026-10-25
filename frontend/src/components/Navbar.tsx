import React from 'react';
import { Program } from '../types';
import {
  LayoutDashboard, Car, Layers, AlertTriangle, FileCheck,
  FlaskConical, AlertCircle, GitPullRequest, Search, HelpCircle
} from 'lucide-react';

export type NavTab =
  | 'dashboard'
  | 'programs'
  | 'parts'
  | 'dfmea'
  | 'dvpr'
  | 'tests'
  | 'issues'
  | 'root_cause'
  | 'changes'
  | 'knowledge';

interface NavbarProps {
  activeTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
  programs: Program[];
  selectedProgramId?: number;
  onSelectProgram: (id?: number) => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  onSelectTab,
  programs,
  selectedProgramId,
  onSelectProgram
}) => {
  const tabs: { id: NavTab; label: string; icon: React.ReactNode }[] = [
    { id: 'dashboard', label: '质量总览', icon: <LayoutDashboard size={16} /> },
    { id: 'programs', label: '车型项目', icon: <Car size={16} /> },
    { id: 'parts', label: '零部件', icon: <Layers size={16} /> },
    { id: 'dfmea', label: 'DFMEA风险', icon: <AlertTriangle size={16} /> },
    { id: 'dvpr', label: 'DVP&R计划', icon: <FileCheck size={16} /> },
    { id: 'tests', label: '试验执行', icon: <FlaskConical size={16} /> },
    { id: 'issues', label: '问题跟踪', icon: <AlertCircle size={16} /> },
    { id: 'root_cause', label: '5-Why分析', icon: <HelpCircle size={16} /> },
    { id: 'changes', label: '工程变更', icon: <GitPullRequest size={16} /> },
    { id: 'knowledge', label: '工程知识库', icon: <Search size={16} /> }
  ];

  return (
    <header style={{
      background: '#0b1329',
      borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
      position: 'sticky',
      top: 0,
      zIndex: 40
    }}>
      {/* Top Banner */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '12px 24px',
        borderBottom: '1px solid rgba(255, 255, 255, 0.05)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            background: 'linear-gradient(135deg, #0284c7, #38bdf8)',
            padding: '8px',
            borderRadius: '8px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 15px rgba(2, 132, 199, 0.4)'
          }}>
            <Car size={22} color="#ffffff" />
          </div>
          <div>
            <div style={{ fontSize: '1.125rem', fontWeight: 700, letterSpacing: '-0.01em', color: '#f8fafc' }}>
              汽车研发工程质量管理平台 <span style={{ fontSize: '0.8rem', color: '#38bdf8', fontWeight: 500 }}>Engineering Quality Lab</span>
            </div>
            <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
              车门 · 车窗 · 尾门 · 密封系统全生命周期验证与闭环质量管理
            </div>
          </div>
        </div>

        {/* Global Vehicle Program Filter */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '0.85rem', color: '#94a3b8' }}>当前项目:</span>
          <select
            className="input-field"
            value={selectedProgramId || ''}
            onChange={(e) => onSelectProgram(e.target.value ? Number(e.target.value) : undefined)}
            style={{ minWidth: '180px', background: '#1e293b' }}
          >
            <option value="">全部车型项目 (全局)</option>
            {programs.map((p) => (
              <option key={p.id} value={p.id}>
                {p.code} - {p.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div style={{
        display: 'flex',
        overflowX: 'auto',
        padding: '0 16px',
        gap: '4px'
      }}>
        {tabs.map((tab) => {
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => onSelectTab(tab.id)}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
                padding: '10px 14px',
                fontSize: '0.875rem',
                fontWeight: isActive ? 600 : 500,
                color: isActive ? '#38bdf8' : '#94a3b8',
                background: 'transparent',
                border: 'none',
                borderBottom: isActive ? '2px solid #38bdf8' : '2px solid transparent',
                cursor: 'pointer',
                whiteSpace: 'nowrap',
                transition: 'all 0.15s ease'
              }}
            >
              {tab.icon}
              {tab.label}
            </button>
          );
        })}
      </div>
    </header>
  );
};
