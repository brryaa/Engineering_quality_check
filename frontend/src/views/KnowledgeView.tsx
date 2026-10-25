import React, { useEffect, useState } from 'react';
import { api } from '../api/client';
import { KnowledgeItem } from '../types';
import { Badge } from '../components/Badge';
import { Plus, Search, BookOpen, Tag, Bookmark, User } from 'lucide-react';

export const KnowledgeView: React.FC = () => {
  const [items, setItems] = useState<KnowledgeItem[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [search, setSearch] = useState<string>('');
  const [categoryFilter, setCategoryFilter] = useState<string>('');
  const [subsystemFilter, setSubsystemFilter] = useState<string>('');
  const [page, setPage] = useState<number>(1);
  const [showModal, setShowModal] = useState<boolean>(false);
  const [expandedId, setExpandedId] = useState<number | null>(null);

  // New Knowledge Item Form state
  const [docCode, setDocCode] = useState('');
  const [title, setTitle] = useState('');
  const [subsystem, setSubsystem] = useState('Primary Body Seal');
  const [category, setCategory] = useState('Lesson-Learned');
  const [tags, setTags] = useState('water-leak,EPDM,sponge-bulb');
  const [content, setContent] = useState('');
  const [keywords, setKeywords] = useState('');
  const [sourceRef, setSourceRef] = useState('');
  const [author, setAuthor] = useState('Dr. Wei Chen');

  const loadData = () => {
    setLoading(true);
    api.getKnowledgeItems({
      page,
      page_size: 20,
      search,
      category: categoryFilter || undefined,
      subsystem: subsystemFilter || undefined
    })
      .then((res) => {
        setItems(res.items);
        setTotal(res.total);
      })
      .catch((err) => alert(`检索工程知识库失败: ${err.message}`))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadData();
  }, [page, search, categoryFilter, subsystemFilter]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createKnowledgeItem({
        doc_code: docCode,
        title,
        subsystem,
        category,
        tags,
        content,
        keywords: keywords || tags.replace(/,/g, ' '),
        source_reference: sourceRef,
        applicable_programs: 'All Vehicle Programs',
        author
      });
      setShowModal(false);
      setDocCode('');
      setTitle('');
      setContent('');
      loadData();
    } catch (err: any) {
      alert(`录入失败: ${err.message}`);
    }
  };

  return (
    <div style={{ padding: '24px', maxWidth: '1440px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Header & Controls */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h1 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#f8fafc' }}>
            工程知识与历史经验库检索 ({total} 篇)
          </h1>
          <p style={{ fontSize: '0.85rem', color: '#94a3b8' }}>
            汽车车身开闭件、无框玻璃防夹、尾门铰链疲劳及车门高压洗车漏水经验教训与标准库
          </p>
        </div>
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
          <div style={{ position: 'relative' }}>
            <Search size={16} style={{ position: 'absolute', left: '10px', top: '10px', color: '#64748b' }} />
            <input
              type="text"
              placeholder="全文字符检索 (如: 漏水 / 防夹 / 铰链 / EPDM)..."
              className="input-field"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{ paddingLeft: '32px', width: '280px' }}
            />
          </div>

          <select
            className="input-field"
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
          >
            <option value="">全部知识类型</option>
            <option value="Lesson-Learned">经验教训 Lesson-Learned</option>
            <option value="Standard-Spec">设计规范 Standard-Spec</option>
            <option value="Failure-Case">失效案例 Failure-Case</option>
            <option value="Best-Practice">最佳实践 Best-Practice</option>
            <option value="Design-Guideline">设计准则 Design-Guideline</option>
          </select>

          <button className="btn-primary" onClick={() => setShowModal(true)}>
            <Plus size={16} /> 沉淀工程知识
          </button>
        </div>
      </div>

      {/* Cards List */}
      {loading ? (
        <div style={{ padding: '40px', textAlign: 'center', color: '#94a3b8' }}>正在检索工程知识库...</div>
      ) : items.length === 0 ? (
        <div style={{ padding: '40px', textAlign: 'center', color: '#94a3b8' }}>未检索到匹配的工程知识或标准指南</div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {items.map((it) => {
            const isExpanded = expandedId === it.id;
            return (
              <div
                key={it.id}
                className="glass-panel"
                style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '12px' }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <BookOpen size={20} color="#38bdf8" />
                    <div>
                      <span style={{ fontSize: '0.75rem', fontFamily: 'monospace', color: '#38bdf8', fontWeight: 600 }}>
                        {it.doc_code}
                      </span>
                      <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: '#f8fafc', marginTop: '2px' }}>
                        {it.title}
                      </h3>
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: '6px' }}>
                    <Badge label={it.category} variant="indigo" />
                    <Badge label={it.subsystem} variant="slate" />
                  </div>
                </div>

                {/* Content preview or full */}
                <div style={{
                  fontSize: '0.9rem',
                  color: '#cbd5e1',
                  lineHeight: '1.6',
                  background: '#090d16',
                  padding: '14px',
                  borderRadius: '8px',
                  border: '1px solid #1e293b'
                }}>
                  {isExpanded ? it.content : `${it.content.slice(0, 180)}...`}
                  <button
                    onClick={() => setExpandedId(isExpanded ? null : it.id)}
                    style={{
                      background: 'none',
                      border: 'none',
                      color: '#38bdf8',
                      cursor: 'pointer',
                      fontSize: '0.85rem',
                      marginLeft: '8px',
                      fontWeight: 600
                    }}
                  >
                    {isExpanded ? '收起详情' : '展开全文阅读'}
                  </button>
                </div>

                {/* Tags and Author */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.8rem', color: '#94a3b8' }}>
                  <div style={{ display: 'flex', gap: '6px', alignItems: 'center', flexWrap: 'wrap' }}>
                    <Tag size={14} color="#818cf8" />
                    {it.tags.split(',').map((tg) => (
                      <span key={tg} style={{ background: '#1e293b', padding: '2px 8px', borderRadius: '4px', fontSize: '0.75rem', color: '#93c5fd' }}>
                        #{tg.trim()}
                      </span>
                    ))}
                  </div>
                  <div style={{ display: 'flex', gap: '12px' }}>
                    <span>规范依据: <strong style={{ color: '#f8fafc' }}>{it.source_reference || '企业内部工程指南'}</strong></span>
                    <span>作者: <strong style={{ color: '#f8fafc' }}>{it.author}</strong></span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Create Modal */}
      {showModal && (
        <div className="modal-overlay">
          <div className="modal-content" style={{ padding: '24px' }}>
            <h2 style={{ fontSize: '1.15rem', fontWeight: 600, color: '#f8fafc', marginBottom: '16px' }}>
              沉淀工程知识与设计准则
            </h2>
            <form onSubmit={handleCreate} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <label style={{ fontSize: '0.8rem', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>文档编号 *</label>
                  <input
                    type="text"
                    required
                    placeholder="如: KB-DOOR-009"
                    className="input-field"
                    value={docCode}
                    onChange={(e) => setDocCode(e.target.value)}
                    style={{ width: '100%' }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '0.8rem', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>分类 *</label>
                  <select
                    className="input-field"
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    style={{ width: '100%' }}
                  >
                    <option value="Lesson-Learned">经验教训 Lesson-Learned</option>
                    <option value="Standard-Spec">设计规范 Standard-Spec</option>
                    <option value="Failure-Case">失效案例 Failure-Case</option>
                    <option value="Best-Practice">最佳实践 Best-Practice</option>
                    <option value="Design-Guideline">设计准则 Design-Guideline</option>
                  </select>
                </div>
              </div>

              <div>
                <label style={{ fontSize: '0.8rem', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>知识标题 *</label>
                <input
                  type="text"
                  required
                  placeholder="如: 无框车门水切条高速风噪消除准则"
                  className="input-field"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  style={{ width: '100%' }}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <label style={{ fontSize: '0.8rem', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>所属子系统</label>
                  <select
                    className="input-field"
                    value={subsystem}
                    onChange={(e) => setSubsystem(e.target.value)}
                    style={{ width: '100%' }}
                  >
                    <option value="Primary Body Seal">Primary Body Seal</option>
                    <option value="Secondary Acoustic Weatherstrip">Secondary Acoustic Weatherstrip</option>
                    <option value="Frameless Window System">Frameless Window System</option>
                    <option value="Power Tailgate System">Power Tailgate System</option>
                    <option value="Front Door Closure">Front Door Closure</option>
                    <option value="Door Hinge & Check Link">Door Hinge & Check Link</option>
                  </select>
                </div>
                <div>
                  <label style={{ fontSize: '0.8rem', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>标签 (逗号分隔)</label>
                  <input
                    type="text"
                    className="input-field"
                    value={tags}
                    onChange={(e) => setTags(e.target.value)}
                    style={{ width: '100%' }}
                  />
                </div>
              </div>

              <div>
                <label style={{ fontSize: '0.8rem', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>知识正文与工程对策 *</label>
                <textarea
                  required
                  rows={4}
                  className="input-field"
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  style={{ width: '100%', resize: 'vertical' }}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <label style={{ fontSize: '0.8rem', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>标准依据 / 来源单号</label>
                  <input
                    type="text"
                    className="input-field"
                    value={sourceRef}
                    onChange={(e) => setSourceRef(e.target.value)}
                    style={{ width: '100%' }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '0.8rem', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>编制工程师</label>
                  <input
                    type="text"
                    className="input-field"
                    value={author}
                    onChange={(e) => setAuthor(e.target.value)}
                    style={{ width: '100%' }}
                  />
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '10px' }}>
                <button type="button" className="btn-secondary" onClick={() => setShowModal(false)}>
                  取消
                </button>
                <button type="submit" className="btn-primary">
                  录入工程知识库
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
