import React, { useState, useEffect } from 'react';
import { Program, User } from '../types';
import { authStorage, api } from '../api/client';
import { LoginModal } from './LoginModal';
import {
  LayoutDashboard, Car, Layers, AlertTriangle, FileCheck,
  FlaskConical, AlertCircle, GitPullRequest, Search, HelpCircle,
  User as UserIcon, LogIn, LogOut, ShieldCheck
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
  const [currentUser, setCurrentUser] = useState<User | null>(authStorage.getUser());
  const [isLoginModalOpen, setIsLoginModalOpen] = useState(false);

  // Auto-authenticate as default admin on first session load if not already logged in
  useEffect(() => {
    if (!authStorage.getToken()) {
      api.login('admin', 'admin123')
        .then((res) => {
          authStorage.setToken(res.access_token);
          authStorage.setUser(res.user);
          setCurrentUser(res.user);
        })
        .catch(() => {
          // If offline/error, proceed gracefully
        });
    } else if (!currentUser) {
      setCurrentUser(authStorage.getUser());
    }
  }, []);

  const handleLogout = () => {
    authStorage.clearToken();
    setCurrentUser(null);
  };

  const getRoleBadge = (role?: string) => {
    switch (role) {
      case 'admin':
        return { label: '系统管理员', bg: 'rgba(129, 140, 248, 0.2)', border: '#818cf8', text: '#c7d2fe' };
      case 'quality_lead':
        return { label: '质量负责人', bg: 'rgba(56, 189, 248, 0.2)', border: '#38bdf8', text: '#bae6fd' };
      case 'design_eng':
      case 'design_engineer':
        return { label: '设计工程师', bg: 'rgba(52, 211, 153, 0.2)', border: '#34d399', text: '#a7f3d0' };
      default:
        return { label: '质量审计员', bg: 'rgba(251, 191, 36, 0.2)', border: '#fbbf24', text: '#fde68a' };
    }
  };

  const badge = getRoleBadge(currentUser?.role);

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
        borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
        flexWrap: 'wrap',
        gap: '12px'
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

        {/* Global Controls & User Auth Indicator */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px', flexWrap: 'wrap' }}>
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

          {/* User Auth & RBAC Badge */}
          {currentUser ? (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              background: '#1e293b',
              padding: '4px 12px',
              borderRadius: '20px',
              border: '1px solid #334155'
            }}>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                fontSize: '0.85rem',
                color: '#f8fafc',
                fontWeight: 600
              }}>
                <UserIcon size={14} color="#38bdf8" />
                <span>{currentUser.full_name || currentUser.username}</span>
              </div>
              <span style={{
                fontSize: '0.75rem',
                padding: '2px 8px',
                borderRadius: '12px',
                background: badge.bg,
                border: `1px solid ${badge.border}`,
                color: badge.text,
                fontWeight: 600
              }}>
                {badge.label}
              </span>
              <button
                type="button"
                onClick={() => setIsLoginModalOpen(true)}
                title="切换角色"
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: '#94a3b8',
                  fontSize: '0.75rem',
                  cursor: 'pointer',
                  textDecoration: 'underline'
                }}
              >
                切换
              </button>
              <button
                type="button"
                onClick={handleLogout}
                title="退出登录"
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: '#f87171',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  padding: '2px'
                }}
              >
                <LogOut size={14} />
              </button>
            </div>
          ) : (
            <button
              type="button"
              onClick={() => setIsLoginModalOpen(true)}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                padding: '6px 14px',
                background: '#0284c7',
                border: 'none',
                borderRadius: '6px',
                color: '#ffffff',
                fontSize: '0.85rem',
                fontWeight: 600,
                cursor: 'pointer'
              }}
            >
              <LogIn size={15} />
              登录 / 切换身份
            </button>
          )}
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

      {/* Authentication Modal */}
      <LoginModal
        isOpen={isLoginModalOpen}
        onClose={() => setIsLoginModalOpen(false)}
        onLoginSuccess={(user) => setCurrentUser(user)}
      />
    </header>
  );
};
