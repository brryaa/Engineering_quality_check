import React, { useEffect, useState } from 'react';
import { api } from './api/client';
import { Program } from './types';
import { Navbar, NavTab } from './components/Navbar';
import { DashboardView } from './views/DashboardView';
import { ProgramsView } from './views/ProgramsView';
import { PartsView } from './views/PartsView';
import { DfmeaView } from './views/DfmeaView';
import { DvprView } from './views/DvprView';
import { TestRunsView } from './views/TestRunsView';
import { IssuesView } from './views/IssuesView';
import { RootCauseView } from './views/RootCauseView';
import { ChangesView } from './views/ChangesView';
import { KnowledgeView } from './views/KnowledgeView';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<NavTab>('dashboard');
  const [programs, setPrograms] = useState<Program[]>([]);
  const [selectedProgramId, setSelectedProgramId] = useState<number | undefined>(undefined);

  useEffect(() => {
    api.getPrograms({ page_size: 100 })
      .then((res) => setPrograms(res.items))
      .catch((err) => console.error('Failed to load vehicle programs', err));
  }, []);

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Navbar
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        programs={programs}
        selectedProgramId={selectedProgramId}
        onSelectProgram={setSelectedProgramId}
      />

      <main style={{ flex: 1, paddingBottom: '40px' }}>
        {activeTab === 'dashboard' && <DashboardView selectedProgramId={selectedProgramId} />}
        {activeTab === 'programs' && <ProgramsView />}
        {activeTab === 'parts' && <PartsView selectedProgramId={selectedProgramId} programs={programs} />}
        {activeTab === 'dfmea' && <DfmeaView selectedProgramId={selectedProgramId} />}
        {activeTab === 'dvpr' && <DvprView selectedProgramId={selectedProgramId} programs={programs} />}
        {activeTab === 'tests' && <TestRunsView />}
        {activeTab === 'issues' && (
          <IssuesView
            selectedProgramId={selectedProgramId}
            onNavigateToRootCause={() => setActiveTab('root_cause')}
          />
        )}
        {activeTab === 'root_cause' && <RootCauseView />}
        {activeTab === 'changes' && <ChangesView selectedProgramId={selectedProgramId} programs={programs} />}
        {activeTab === 'knowledge' && <KnowledgeView />}
      </main>

      {/* Footer */}
      <footer style={{
        padding: '16px 24px',
        borderTop: '1px solid rgba(255, 255, 255, 0.05)',
        textAlign: 'center',
        fontSize: '0.8rem',
        color: '#64748b'
      }}>
        汽车研发工程质量管理平台 (Engineering Quality Lab) · Automotive Closures & Sealing Systems
      </footer>
    </div>
  );
};

export default App;
