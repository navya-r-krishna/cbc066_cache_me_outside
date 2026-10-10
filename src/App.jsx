import React, { useState } from 'react';
import { AppProvider, useApp } from './context/AppContext';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { DashboardView } from './components/Dashboard/DashboardView';
import { GenerateView } from './components/Generate/GenerateView';
import { QuestionLibraryView } from './components/Library/QuestionLibraryView';
import { SettingsView } from './components/Settings/SettingsView';
import { ToastContainer } from './components/Common/Toast';
import './App.css';

function MainAppContent() {
  const { currentTab } = useApp();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const renderCurrentView = () => {
    switch (currentTab) {
      case 'dashboard':
        return <DashboardView />;
      case 'library':
        return <QuestionLibraryView />;
      default:
        return <DashboardView />;
    }
  };

  return (
    <div className="app-layout">
      {/* Dark Sidebar */}
      <Sidebar
        mobileOpen={mobileMenuOpen}
        onCloseMobile={() => setMobileMenuOpen(false)}
      />

      {/* Main Content Workspace */}
      <div className="main-wrapper">
        <Header onOpenMobile={() => setMobileMenuOpen(true)} />
        <main className="content-body" id="main-content">
          {renderCurrentView()}
        </main>
      </div>

      {/* Toast Notifications System */}
      <ToastContainer />
    </div>
  );
}

function App() {
  return (
    <AppProvider>
      <MainAppContent />
    </AppProvider>
  );
}

export default App;
