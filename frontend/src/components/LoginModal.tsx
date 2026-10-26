import React, { useState } from 'react';
import { api, authStorage } from '../api/client';
import { User } from '../types';
import { Lock, User as UserIcon, Shield, CheckCircle2, AlertCircle } from 'lucide-react';

interface LoginModalProps {
  isOpen: boolean;
  onClose: () => void;
  onLoginSuccess: (user: User) => void;
}

export const LoginModal: React.FC<LoginModalProps> = ({
  isOpen,
  onClose,
  onLoginSuccess
}) => {
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('admin123');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleLogin = async (u?: string, p?: string) => {
    const userToLogin = u || username;
    const passToLogin = p || password;
    setLoading(true);
    setError(null);
    try {
      const res = await api.login(userToLogin, passToLogin);
      authStorage.setToken(res.access_token);
      authStorage.setUser(res.user);
      onLoginSuccess(res.user);
      onClose();
    } catch (err: any) {
      setError(err.message || '登录失败，请检查用户名和密码。');
    } finally {
      setLoading(false);
    }
  };

  const quickRoles = [
    { role: '系统管理员 (Admin)', user: 'admin', pass: 'admin123', color: '#818cf8', desc: '拥有全部增删改查、用户配置与工程变更终审权限' },
    { role: '质量负责人 (Quality Lead)', user: 'quality_lead', pass: 'quality123', color: '#38bdf8', desc: '具备工程变更(ECR/ECO)审批与发布、DVP&R审核权限' },
    { role: '设计工程师 (Design Engineer)', user: 'design_eng', pass: 'engineer123', color: '#34d399', desc: '可创建与维护车型、零部件、DFMEA，起草工程变更' },
    { role: '质量审计员 (Auditor)', user: 'auditor', pass: 'audit123', color: '#fbbf24', desc: '只读审计权限，受限无法执行修改和删除操作' }
  ];

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.75)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 100,
      backdropFilter: 'blur(4px)'
    }}>
      <div style={{
        background: '#0f172a',
        border: '1px solid #334155',
        borderRadius: '12px',
        width: '460px',
        maxWidth: '90vw',
        padding: '24px',
        color: '#f8fafc',
        boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.5)'
      }}>
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '20px' }}>
          <div style={{
            background: 'linear-gradient(135deg, #0284c7, #38bdf8)',
            padding: '8px',
            borderRadius: '8px'
          }}>
            <Lock size={20} color="#fff" />
          </div>
          <div>
            <h3 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 600 }}>平台身份登录与权限切换</h3>
            <p style={{ margin: 0, fontSize: '0.8rem', color: '#94a3b8' }}>选择预置工程角色或输入账号凭证</p>
          </div>
        </div>

        {error && (
          <div style={{
            background: 'rgba(239, 68, 68, 0.15)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: '6px',
            padding: '10px 14px',
            marginBottom: '16px',
            fontSize: '0.85rem',
            color: '#fca5a5',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}>
            <AlertCircle size={16} />
            <span>{error}</span>
          </div>
        )}

        {/* Quick preset roles */}
        <div style={{ marginBottom: '20px' }}>
          <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#94a3b8', marginBottom: '8px' }}>
            快速切换测试身份 (Quick Preset Roles):
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {quickRoles.map((qr) => (
              <button
                key={qr.user}
                type="button"
                onClick={() => {
                  setUsername(qr.user);
                  setPassword(qr.pass);
                  handleLogin(qr.user, qr.pass);
                }}
                disabled={loading}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '8px 12px',
                  background: '#1e293b',
                  border: '1px solid #334155',
                  borderRadius: '6px',
                  color: '#f8fafc',
                  cursor: 'pointer',
                  textAlign: 'left',
                  transition: 'background 0.15s ease'
                }}
              >
                <div>
                  <div style={{ fontSize: '0.85rem', fontWeight: 600, color: qr.color }}>{qr.role}</div>
                  <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>{qr.desc}</div>
                </div>
                <div style={{ fontSize: '0.75rem', color: '#64748b' }}>{qr.user}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Standard credentials form */}
        <form onSubmit={(e) => { e.preventDefault(); handleLogin(); }}>
          <div style={{ marginBottom: '14px' }}>
            <label style={{ display: 'block', fontSize: '0.85rem', marginBottom: '6px', color: '#cbd5e1' }}>
              用户名 (Username)
            </label>
            <div style={{ position: 'relative' }}>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                style={{
                  width: '100%',
                  padding: '8px 12px 8px 34px',
                  background: '#1e293b',
                  border: '1px solid #475569',
                  borderRadius: '6px',
                  color: '#f8fafc',
                  boxSizing: 'border-box'
                }}
              />
              <UserIcon size={16} color="#64748b" style={{ position: 'absolute', left: '10px', top: '10px' }} />
            </div>
          </div>

          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', fontSize: '0.85rem', marginBottom: '6px', color: '#cbd5e1' }}>
              登录密码 (Password)
            </label>
            <div style={{ position: 'relative' }}>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                style={{
                  width: '100%',
                  padding: '8px 12px 8px 34px',
                  background: '#1e293b',
                  border: '1px solid #475569',
                  borderRadius: '6px',
                  color: '#f8fafc',
                  boxSizing: 'border-box'
                }}
              />
              <Lock size={16} color="#64748b" style={{ position: 'absolute', left: '10px', top: '10px' }} />
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
            <button
              type="button"
              onClick={onClose}
              style={{
                padding: '8px 16px',
                background: 'transparent',
                border: '1px solid #475569',
                borderRadius: '6px',
                color: '#cbd5e1',
                cursor: 'pointer'
              }}
            >
              取消
            </button>
            <button
              type="submit"
              disabled={loading}
              style={{
                padding: '8px 20px',
                background: '#0284c7',
                border: 'none',
                borderRadius: '6px',
                color: '#ffffff',
                fontWeight: 600,
                cursor: 'pointer'
              }}
            >
              {loading ? '验证中...' : '确认登录'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
