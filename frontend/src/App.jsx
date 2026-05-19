import React, { useState, useEffect } from 'react';
import { 
  BarChart3, Users, BookOpen, Send, LogOut, Search, ShieldAlert, Check, 
  Trash2, X, RefreshCw, AlertTriangle, Play, Calendar, UserMinus, UserCheck, Activity, Clock
} from 'lucide-react';
import { 
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Bar, Cell
} from 'recharts';

export default function App() {
  const [token, setToken] = useState(localStorage.getItem('admin_token') || '');
  const [activeTab, setActiveTab] = useState('analytics');
  const [dashboardData, setDashboardData] = useState(null);
  
  // Tab states
  const [usersList, setUsersList] = useState([]);
  const [userTotal, setUserTotal] = useState(0);
  const [usersPage, setUsersPage] = useState(1);
  const [usersSearch, setUsersSearch] = useState('');
  const [usersStatus, setUsersStatus] = useState('');
  
  const [quizzesList, setQuizzesList] = useState([]);
  const [selectedQuiz, setSelectedQuiz] = useState(null);
  
  const [broadcasts, setBroadcasts] = useState([]);
  const [bcText, setBcText] = useState('');
  const [bcType, setBcType] = useState('text');
  const [bcMedia, setBcMedia] = useState('');
  const [bcBtnText, setBcBtnText] = useState('');
  const [bcBtnUrl, setBcBtnUrl] = useState('');
  const [bcSchedule, setBcSchedule] = useState('');
  const [selectedBroadcastForTargets, setSelectedBroadcastForTargets] = useState(null);
  
  const [isStealth, setIsStealth] = useState(true);
  const [authError, setAuthError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const [loading, setLoading] = useState(false);

  // Parse path for Token (Stealth Mechanism)
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const urlToken = urlParams.get('token');
    
    if (urlToken) {
      setIsStealth(false);
      handleTokenLogin(urlToken);
    } else if (token) {
      setIsStealth(false);
      fetchDashboard();
    } else {
      // If no token or stored JWT, stay in stealth mode (displays 404 to non-admins)
      setIsStealth(true);
    }
  }, [token]);

  const handleTokenLogin = async (loginToken) => {
    try {
      setLoading(true);
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token: loginToken })
      });
      
      const data = await res.json();
      if (res.ok) {
        localStorage.setItem('admin_token', data.access_token);
        setToken(data.access_token);
        setSuccessMsg("Sessiya muvaffaqiyatli boshlandi!");
        // Clear query parameters
        window.history.replaceState({}, document.title, window.location.pathname);
      } else {
        setAuthError(data.detail || "Kirish tokeni noto'g'ri yoki muddati tugagan.");
      }
    } catch (e) {
      setAuthError("Tizimga bog'lanishda xatolik.");
    } finally {
      setLoading(false);
    }
  };

  // Helper fetch config with JWT bearer
  const authFetch = async (url, options = {}) => {
    const headers = {
      'Authorization': `Bearer ${token}`,
      ...options.headers
    };
    if (options.body && !(options.body instanceof FormData)) {
      headers['Content-Type'] = 'application/json';
    }
    
    try {
      const res = await fetch(url, { ...options, headers });
      if (res.status === 401) {
        // Expired session
        handleLogout();
        return { error: "Sessiya muddati tugadi." };
      }
      return res;
    } catch (e) {
      return { error: "Xatolik yuz berdi." };
    }
  };

  const fetchDashboard = async () => {
    if (!token) return;
    try {
      const res = await authFetch('/api/analytics/dashboard');
      if (res.error) return;
      const data = await res.json();
      setDashboardData(data);
    } catch (e) {
      console.error(e);
    }
  };

  const fetchUsers = async () => {
    if (!token) return;
    try {
      let url = `/api/users?page=${usersPage}&limit=12`;
      if (usersSearch) url += `&search=${encodeURIComponent(usersSearch)}`;
      if (usersStatus) url += `&status_filter=${usersStatus}`;
      
      const res = await authFetch(url);
      if (res.error) return;
      const data = await res.json();
      setUsersList(data.users || []);
      setUserTotal(data.total || 0);
    } catch (e) {
      console.error(e);
    }
  };

  const fetchQuizzes = async () => {
    if (!token) return;
    try {
      const res = await authFetch('/api/quizzes');
      if (res.error) return;
      const data = await res.json();
      setQuizzesList(data || []);
    } catch (e) {
      console.error(e);
    }
  };

  const fetchBroadcasts = async () => {
    if (!token) return;
    try {
      const res = await authFetch('/api/broadcast');
      if (res.error) return;
      const data = await res.json();
      setBroadcasts(data || []);
    } catch (e) {
      console.error(e);
    }
  };

  // Poll for live broadcast progress & dashboard updates
  useEffect(() => {
    if (!token) return;
    
    fetchDashboard();
    
    const interval = setInterval(() => {
      fetchDashboard();
      if (activeTab === 'broadcast') {
        fetchBroadcasts();
      }
    }, 4000); // Live real-time updates every 4 seconds!
    
    return () => clearInterval(interval);
  }, [token, activeTab]);

  // Handle Tab Loading
  useEffect(() => {
    if (!token) return;
    if (activeTab === 'users') {
      fetchUsers();
    } else if (activeTab === 'quizzes') {
      fetchQuizzes();
    } else if (activeTab === 'broadcast') {
      fetchBroadcasts();
    }
  }, [token, activeTab, usersPage, usersSearch, usersStatus]);

  const handleLogout = () => {
    localStorage.removeItem('admin_token');
    setToken('');
    setIsStealth(true);
    setAuthError('');
  };

  const handleBlockUser = async (userId) => {
    try {
      const res = await authFetch(`/api/users/${userId}/block`, { method: 'POST' });
      if (res.ok) {
        fetchUsers();
        setSuccessMsg("Foydalanuvchi statusi yangilandi!");
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleDeleteQuiz = async (quizId) => {
    if (!confirm("Ushbu testni butunlay o'chirmoqchimisiz? Barcha natijalar yo'qoladi!")) return;
    try {
      const res = await authFetch(`/api/quizzes/${quizId}`, { method: 'DELETE' });
      if (res.ok) {
        fetchQuizzes();
        setSuccessMsg("Test muvaffaqiyatli o'chirildi!");
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleSendBroadcast = async (e) => {
    e.preventDefault();
    if (!bcText) return;
    
    const payload = {
      type: bcType,
      content: bcType === 'text' ? bcText : bcMedia,
      buttons: bcBtnText && bcBtnUrl ? [{ text: bcBtnText, url: bcBtnUrl }] : null,
      scheduled_at: bcSchedule ? new Date(bcSchedule).toISOString() : null
    };

    if (bcType !== 'text') {
      // In media broadcasts, we append the caption text as part of the content payload or separate it.
      // For development, we store media URL or file ID, and use bcText as content if appropriate, or store caption inside content.
      // Let's store media in content, or let content be a JSON of media + text caption.
      payload.content = JSON.stringify({ media: bcMedia, text: bcText });
    }
    
    try {
      const res = await authFetch('/api/broadcast', {
        method: 'POST',
        body: JSON.stringify(payload)
      });
      
      if (res.ok) {
        setBcText('');
        setBcMedia('');
        setBcBtnText('');
        setBcBtnUrl('');
        setBcSchedule('');
        fetchBroadcasts();
        setSuccessMsg("Broadcast muvaffaqiyatli saqlandi va yuborilmoqda!");
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleCancelBroadcast = async (bcId) => {
    try {
      const res = await authFetch(`/api/broadcast/${bcId}/cancel`, { method: 'POST' });
      if (res.ok) {
        fetchBroadcasts();
        setSuccessMsg("Yuborish bekor qilindi!");
      }
    } catch (e) {
      console.error(e);
    }
  };

  // Toast auto-clear
  useEffect(() => {
    if (successMsg) {
      const t = setTimeout(() => setSuccessMsg(''), 4000);
      return () => clearTimeout(t);
    }
  }, [successMsg]);

  // Stealth 404 UI for normal users to maintain hidden admin state
  if (isStealth) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-darkBg text-gray-400 p-6 text-center select-none relative">
        <div className="glow-spot-1"></div>
        <div className="glow-spot-2"></div>
        
        {authError ? (
          <div className="glass-card p-8 rounded-2xl max-w-md w-full border border-red-500/30 animate-pulse">
            <ShieldAlert className="w-16 h-16 text-red-500 mx-auto mb-4" />
            <h1 className="text-2xl font-bold text-white mb-2">Kirish Rad Etildi</h1>
            <p className="text-sm text-gray-400 mb-6">{authError}</p>
            <button 
              onClick={() => { setAuthError(''); window.location.reload(); }}
              className="px-6 py-2 bg-gradient-to-r from-red-600 to-pink-600 text-white rounded-lg text-sm font-semibold transition hover:opacity-90"
            >
              Qayta Urinish
            </button>
          </div>
        ) : (
          <div className="max-w-md">
            <h1 className="text-9xl font-black text-neonViolet/30 tracking-widest mb-4">404</h1>
            <h2 className="text-2xl font-bold text-white mb-2">Sahifa Topilmadi</h2>
            <p className="text-sm text-gray-500 mb-6">
              Siz so'rayotgan manzil ushbu serverda mavjud emas yoki sizda kirish huquqi yo'q.
            </p>
            <a 
              href="https://t.me" 
              className="inline-block px-6 py-3 bg-neonViolet/20 border border-neonViolet/40 hover:bg-neonViolet/30 text-neonViolet font-medium rounded-lg text-sm transition"
            >
              Telegramga qaytish
            </a>
          </div>
        )}
      </div>
    );
  }

  // Dashboard Main Panel UI
  return (
    <div className="min-h-screen bg-darkBg text-gray-100 flex relative overflow-hidden font-outfit">
      {/* Floating neon ambient dots */}
      <div className="glow-spot-1"></div>
      <div className="glow-spot-2"></div>

      {/* Floating Success Toast */}
      {successMsg && (
        <div className="fixed bottom-6 right-6 z-50 glass-card border-green-500/40 bg-green-950/20 px-6 py-3 rounded-xl flex items-center gap-3 shadow-lg shadow-green-950/10 animate-bounce">
          <div className="w-6 h-6 rounded-full bg-green-500 flex items-center justify-center text-white">
            <Check className="w-4 h-4" />
          </div>
          <span className="text-sm font-medium text-white">{successMsg}</span>
        </div>
      )}

      {/* Left Sidebar Navigation */}
      <aside className="w-72 bg-darkBg/90 border-r border-neonViolet/10 p-6 flex flex-col justify-between z-10 backdrop-blur-md">
        <div>
          <div className="flex items-center gap-3 mb-10 px-2">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-neonViolet to-neonPink flex items-center justify-center text-white font-black text-xl shadow-lg neon-glow-violet">
              P
            </div>
            <div>
              <h1 className="font-extrabold text-lg text-white leading-tight tracking-wider">POOLBOT</h1>
              <span className="text-[10px] text-neonViolet font-semibold uppercase tracking-widest">SaaS Dashboard</span>
            </div>
          </div>

          <nav className="space-y-2">
            <button
              onClick={() => setActiveTab('analytics')}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-semibold transition ${
                activeTab === 'analytics' 
                  ? 'bg-gradient-to-r from-neonViolet/20 to-neonPink/10 text-white border-l-4 border-neonViolet' 
                  : 'text-gray-400 hover:bg-white/5 hover:text-white'
              }`}
            >
              <BarChart3 className="w-5 h-5 text-neonViolet" />
              Analitika
            </button>
            <button
              onClick={() => setActiveTab('users')}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-semibold transition ${
                activeTab === 'users' 
                  ? 'bg-gradient-to-r from-neonViolet/20 to-neonPink/10 text-white border-l-4 border-neonViolet' 
                  : 'text-gray-400 hover:bg-white/5 hover:text-white'
              }`}
            >
              <Users className="w-5 h-5 text-neonViolet" />
              Foydalanuvchilar
            </button>
            <button
              onClick={() => setActiveTab('quizzes')}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-semibold transition ${
                activeTab === 'quizzes' 
                  ? 'bg-gradient-to-r from-neonViolet/20 to-neonPink/10 text-white border-l-4 border-neonViolet' 
                  : 'text-gray-400 hover:bg-white/5 hover:text-white'
              }`}
            >
              <BookOpen className="w-5 h-5 text-neonViolet" />
              Testlar Boshqaruvi
            </button>
            <button
              onClick={() => setActiveTab('broadcast')}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-semibold transition ${
                activeTab === 'broadcast' 
                  ? 'bg-gradient-to-r from-neonViolet/20 to-neonPink/10 text-white border-l-4 border-neonViolet' 
                  : 'text-gray-400 hover:bg-white/5 hover:text-white'
              }`}
            >
              <Send className="w-5 h-5 text-neonViolet" />
              Broadcast Tizimi
            </button>
          </nav>
        </div>

        <div className="border-t border-neonViolet/10 pt-6">
          <div className="flex items-center gap-3 px-2 mb-6">
            <div className="w-8 h-8 rounded-full bg-neonViolet/30 flex items-center justify-center text-white font-bold text-xs uppercase">
              AD
            </div>
            <div>
              <p className="text-xs font-bold text-white">Administrator</p>
              <span className="text-[10px] text-green-500 font-semibold flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-ping"></span>
                Online
              </span>
            </div>
          </div>
          <button 
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-4 py-3 text-red-400 hover:bg-red-950/20 hover:text-red-300 rounded-xl text-sm font-semibold transition"
          >
            <LogOut className="w-5 h-5" />
            Tizimdan Chiqish
          </button>
        </div>
      </aside>

      {/* Main Panel Content Area */}
      <main className="flex-1 p-10 overflow-y-auto max-h-screen z-10">
        
        {/* HEADER BAR */}
        <header className="flex items-center justify-between mb-10 pb-6 border-b border-neonViolet/5">
          <div>
            <span className="text-xs text-neonViolet font-bold tracking-widest uppercase">Admin Control Panel</span>
            <h2 className="text-3xl font-extrabold text-white">
              {activeTab === 'analytics' && "📈 Analitika va Tahlillar"}
              {activeTab === 'users' && "👥 Foydalanuvchilar Statistikasi"}
              {activeTab === 'quizzes' && "📚 Test Savollari Boshqaruvi"}
              {activeTab === 'broadcast' && "📢 Broadcast Xabarnomalar"}
            </h2>
          </div>
          
          <div className="flex items-center gap-4">
            {dashboardData?.online_sessions_count > 0 && (
              <div className="glass-card bg-neonPink/5 border-neonPink/20 px-4 py-2 rounded-xl flex items-center gap-2 text-xs font-bold text-neonPink tracking-wider uppercase animate-pulse">
                <Clock className="w-4 h-4" />
                Live: {dashboardData.online_sessions_count} ta aktiv test
              </div>
            )}
            <button 
              onClick={() => {
                fetchDashboard();
                if (activeTab === 'users') fetchUsers();
                if (activeTab === 'quizzes') fetchQuizzes();
                if (activeTab === 'broadcast') fetchBroadcasts();
                setSuccessMsg("Ma'lumotlar yangilandi!");
              }}
              className="p-3 bg-neonViolet/10 hover:bg-neonViolet/20 border border-neonViolet/20 text-neonViolet hover:text-white rounded-xl transition"
            >
              <RefreshCw className="w-5 h-5" />
            </button>
          </div>
        </header>

        {/* 1. ANALYTICS BOARD PANEL */}
        {activeTab === 'analytics' && dashboardData && (
          <div className="space-y-10">
            {/* Quick Metrics Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
              <div className="glass-card p-6 rounded-2xl relative overflow-hidden">
                <span className="text-xs text-gray-400 font-semibold tracking-wider">Jami Userlar</span>
                <p className="text-3xl font-black text-white mt-2">{dashboardData.total_users}</p>
                <div className="absolute right-4 bottom-4 text-neonViolet/10">
                  <Users className="w-12 h-12" />
                </div>
              </div>
              <div className="glass-card p-6 rounded-2xl relative overflow-hidden">
                <span className="text-xs text-gray-400 font-semibold tracking-wider">Kunlik Faol (DAU)</span>
                <p className="text-3xl font-black text-white mt-2">{dashboardData.active_users.daily}</p>
                <div className="absolute right-4 bottom-4 text-neonViolet/10">
                  <Activity className="w-12 h-12" />
                </div>
              </div>
              <div className="glass-card p-6 rounded-2xl relative overflow-hidden">
                <span className="text-xs text-gray-400 font-semibold tracking-wider">Haftalik (WAU)</span>
                <p className="text-3xl font-black text-white mt-2">{dashboardData.active_users.weekly}</p>
                <div className="absolute right-4 bottom-4 text-neonViolet/10">
                  <Activity className="w-12 h-12" />
                </div>
              </div>
              <div className="glass-card p-6 rounded-2xl relative overflow-hidden">
                <span className="text-xs text-gray-400 font-semibold tracking-wider">Bitirilgan Testlar</span>
                <p className="text-3xl font-black text-white mt-2">{dashboardData.quiz_stats.total_completions}</p>
                <div className="absolute right-4 bottom-4 text-neonViolet/10">
                  <Check className="w-12 h-12" />
                </div>
              </div>
              <div className="glass-card p-6 rounded-2xl relative overflow-hidden">
                <span className="text-xs text-gray-400 font-semibold tracking-wider">O'rtacha Ball</span>
                <p className="text-3xl font-black text-white mt-2">{dashboardData.quiz_stats.average_score} ta</p>
                <div className="absolute right-4 bottom-4 text-neonViolet/10">
                  <BarChart3 className="w-12 h-12" />
                </div>
              </div>
            </div>

            {/* Growth Chart */}
            <div className="glass-card p-8 rounded-2xl">
              <h3 className="text-lg font-bold text-white mb-6">User Growth - Oxirgi 15 kunlik o'sish</h3>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={dashboardData.user_growth}>
                    <defs>
                      <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#9d4edd" stopOpacity={0.4}/>
                        <stop offset="95%" stopColor="#9d4edd" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#251b3a" />
                    <XAxis dataKey="date" stroke="#9d4edd" />
                    <YAxis stroke="#9d4edd" />
                    <Tooltip contentStyle={{ backgroundColor: '#130b24', borderColor: '#9d4edd', borderRadius: '12px' }} />
                    <Area type="monotone" dataKey="count" stroke="#9d4edd" strokeWidth={3} fillOpacity={1} fill="url(#colorCount)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Sub-grid tables */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              
              {/* Most Active Users */}
              <div className="glass-card p-6 rounded-2xl">
                <h3 className="text-lg font-bold text-white mb-4">🏆 Eng Aktiv Foydalanuvchilar</h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-left border-collapse">
                    <thead>
                      <tr className="border-b border-neonViolet/10 text-gray-400 text-xs uppercase">
                        <th className="py-3 px-2">Foydalanuvchi</th>
                        <th className="py-3 px-2 text-center">Javoblar</th>
                        <th className="py-3 px-2 text-right">Jami Ball</th>
                      </tr>
                    </thead>
                    <tbody>
                      {dashboardData.most_active_users.map((u, i) => (
                        <tr key={i} className="border-b border-neonViolet/5 text-sm hover:bg-white/5 transition">
                          <td className="py-3 px-2">
                            <p className="font-semibold text-white">{u.name}</p>
                            <span className="text-xs text-gray-500">@{u.username}</span>
                          </td>
                          <td className="py-3 px-2 text-center font-bold text-neonViolet">{u.completions} ta test</td>
                          <td className="py-3 px-2 text-right font-black text-neonPink">{u.total_score}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Most Used Quizzes */}
              <div className="glass-card p-6 rounded-2xl">
                <h3 className="text-lg font-bold text-white mb-4">🔥 Eng Ko'p Ishlangan Testlar</h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-left border-collapse">
                    <thead>
                      <tr className="border-b border-neonViolet/10 text-gray-400 text-xs uppercase">
                        <th className="py-3 px-2">Test Nomi</th>
                        <th className="py-3 px-2 text-right">Ishlanish soni</th>
                      </tr>
                    </thead>
                    <tbody>
                      {dashboardData.most_used_quizzes.map((q, i) => (
                        <tr key={i} className="border-b border-neonViolet/5 text-sm hover:bg-white/5 transition">
                          <td className="py-3 px-2 font-semibold text-white">{q.title}</td>
                          <td className="py-3 px-2 text-right font-bold text-neonPink">{q.usage} marta</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>

            {/* Admin Logs Timeline */}
            <div className="glass-card p-6 rounded-2xl">
              <h3 className="text-lg font-bold text-white mb-6">🪵 Admin Faollik Jurnali</h3>
              <div className="space-y-4">
                {dashboardData.recent_logs.map((log, i) => (
                  <div key={i} className="flex gap-4 items-start p-3 bg-white/5 hover:bg-white/10 rounded-xl transition border border-white/5">
                    <div className="text-xs px-2.5 py-1 bg-neonViolet/20 border border-neonViolet/30 text-neonViolet font-bold uppercase rounded-lg">
                      {log.action}
                    </div>
                    <div className="flex-1">
                      <p className="text-sm text-gray-200">{log.details}</p>
                      <span className="text-[10px] text-gray-500">{log.created_at}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

          </div>
        )}

        {/* 2. USERS MANAGEMENT PANEL */}
        {activeTab === 'users' && (
          <div className="space-y-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div className="flex items-center gap-4 bg-darkCard/80 border border-neonViolet/20 rounded-xl px-4 py-2 w-full md:w-96 backdrop-blur-md">
                <Search className="w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  placeholder="ID, ism yoki username orqali qidiring..."
                  className="bg-transparent border-none outline-none text-sm w-full text-white placeholder-gray-500"
                  value={usersSearch}
                  onChange={(e) => { setUsersSearch(e.target.value); setUsersPage(1); }}
                />
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => { setUsersStatus(''); setUsersPage(1); }}
                  className={`px-4 py-2 rounded-xl text-xs font-bold uppercase tracking-wider transition ${
                    usersStatus === '' ? 'bg-neonViolet text-white' : 'bg-white/5 text-gray-400 hover:text-white'
                  }`}
                >
                  Barchasi
                </button>
                <button
                  onClick={() => { setUsersStatus('active'); setUsersPage(1); }}
                  className={`px-4 py-2 rounded-xl text-xs font-bold uppercase tracking-wider transition ${
                    usersStatus === 'active' ? 'bg-green-600 text-white' : 'bg-white/5 text-gray-400 hover:text-white'
                  }`}
                >
                  Faol
                </button>
                <button
                  onClick={() => { setUsersStatus('blocked'); setUsersPage(1); }}
                  className={`px-4 py-2 rounded-xl text-xs font-bold uppercase tracking-wider transition ${
                    usersStatus === 'blocked' ? 'bg-red-600 text-white' : 'bg-white/5 text-gray-400 hover:text-white'
                  }`}
                >
                  Bloklangan
                </button>
              </div>
            </div>

            <div className="glass-card rounded-2xl overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-neonViolet/10 text-gray-400 text-xs uppercase bg-white/5">
                      <th className="py-4 px-6">ID / Username</th>
                      <th className="py-4 px-6">Foydalanuvchi ismi</th>
                      <th className="py-4 px-6">Ro'yxatdan o'tgan</th>
                      <th className="py-4 px-6 text-center">Ishlangan testlar</th>
                      <th className="py-4 px-6 text-center">Status</th>
                      <th className="py-4 px-6 text-right">Amallar</th>
                    </tr>
                  </thead>
                  <tbody>
                    {usersList.map((user) => (
                      <tr key={user.id} className="border-b border-neonViolet/5 text-sm hover:bg-white/5 transition">
                        <td className="py-4 px-6">
                          <p className="font-mono text-xs text-gray-300">{user.id}</p>
                          <span className="text-xs text-neonViolet">@{user.username || 'No username'}</span>
                        </td>
                        <td className="py-4 px-6 font-semibold text-white">
                          {user.first_name} {user.last_name || ''}
                        </td>
                        <td className="py-4 px-6 text-xs text-gray-400">
                          {new Date(user.created_at).toLocaleDateString('uz-UZ')}
                        </td>
                        <td className="py-4 px-6 text-center font-bold text-neonPink">
                          {user.completions_count} ta
                        </td>
                        <td className="py-4 px-6 text-center">
                          <span className={`px-3 py-1 rounded-full text-[10px] font-extrabold uppercase ${
                            user.is_blocked 
                              ? 'bg-red-500/10 text-red-400 border border-red-500/30' 
                              : 'bg-green-500/10 text-green-400 border border-green-500/30'
                          }`}>
                            {user.is_blocked ? "Bloklangan" : "Faol"}
                          </span>
                        </td>
                        <td className="py-4 px-6 text-right">
                          <button
                            onClick={() => handleBlockUser(user.id)}
                            className={`p-2 rounded-lg transition ${
                              user.is_blocked 
                                ? 'bg-green-600/20 text-green-400 border border-green-500/40 hover:bg-green-600' 
                                : 'bg-red-600/20 text-red-400 border border-red-500/40 hover:bg-red-600'
                            } hover:text-white`}
                            title={user.is_blocked ? "Blokdan chiqarish" : "Bloklash"}
                          >
                            {user.is_blocked ? <UserCheck className="w-4 h-4" /> : <UserMinus className="w-4 h-4" />}
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              <div className="flex items-center justify-between p-6 border-t border-neonViolet/10 bg-white/5">
                <span className="text-xs text-gray-400">Jami: {userTotal} ta foydalanuvchi</span>
                <div className="flex items-center gap-2">
                  <button
                    disabled={usersPage <= 1}
                    onClick={() => setUsersPage(usersPage - 1)}
                    className="px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-xs font-semibold disabled:opacity-50 hover:bg-neonViolet/20"
                  >
                    Oldingi
                  </button>
                  <span className="text-xs font-bold px-3 py-2 bg-neonViolet/20 rounded-lg text-neonViolet">
                    Sahifa {usersPage}
                  </span>
                  <button
                    disabled={usersList.length < 12}
                    onClick={() => setUsersPage(usersPage + 1)}
                    className="px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-xs font-semibold disabled:opacity-50 hover:bg-neonViolet/20"
                  >
                    Keyingi
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* 3. QUIZZES MANAGEMENT PANEL */}
        {activeTab === 'quizzes' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {quizzesList.map((quiz) => (
                <div key={quiz.id} className="glass-card p-6 rounded-2xl glass-card-hover flex flex-col justify-between h-56">
                  <div>
                    <div className="flex justify-between items-start mb-3">
                      <span className="text-[10px] bg-neonViolet/20 border border-neonViolet/30 text-neonViolet px-2 py-1 rounded font-bold uppercase">
                        {quiz.total_questions} ta savol
                      </span>
                      <span className="text-[10px] text-gray-500">
                        {new Date(quiz.created_at).toLocaleDateString('uz-UZ')}
                      </span>
                    </div>
                    <h3 className="text-lg font-bold text-white mb-2 leading-snug line-clamp-2">{quiz.title}</h3>
                    <p className="text-xs text-gray-400 mb-4">Yuklovchi: <span className="text-neonPink font-medium">@{quiz.creator_name}</span></p>
                  </div>

                  <div className="flex items-center justify-between border-t border-neonViolet/10 pt-4">
                    <span className="text-xs text-gray-400 font-medium">
                      🎯 {quiz.total_sessions} marta ishlandi
                    </span>
                    
                    <div className="flex items-center gap-2">
                      <button 
                        onClick={() => setSelectedQuiz(quiz)}
                        className="px-3 py-1.5 bg-neonViolet/20 border border-neonViolet/30 hover:bg-neonViolet text-neonViolet hover:text-white rounded-lg text-xs font-bold transition"
                      >
                        Savollar
                      </button>
                      <button
                        onClick={() => handleDeleteQuiz(quiz.id)}
                        className="p-1.5 bg-red-600/20 border border-red-500/30 hover:bg-red-600 text-red-400 hover:text-white rounded-lg transition"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
            
            {/* Modal for Quiz Questions detail */}
            {selectedQuiz && (
              <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-6 backdrop-blur-sm">
                <div className="glass-card w-full max-w-2xl rounded-2xl overflow-hidden border border-neonViolet/30 flex flex-col max-h-[85vh]">
                  <header className="flex justify-between items-center p-6 border-b border-neonViolet/10 bg-white/5">
                    <div>
                      <span className="text-xs text-neonViolet font-bold tracking-widest uppercase">Test Savollari</span>
                      <h3 className="text-xl font-extrabold text-white leading-tight">{selectedQuiz.title}</h3>
                    </div>
                    <button 
                      onClick={() => setSelectedQuiz(null)}
                      className="p-2 hover:bg-white/5 rounded-full text-gray-400 hover:text-white"
                    >
                      <X className="w-5 h-5" />
                    </button>
                  </header>
                  
                  <div className="p-6 overflow-y-auto space-y-6 flex-1">
                    {/* Render questions dynamically */}
                    <QuizQuestionsList quizId={selectedQuiz.id} authFetch={authFetch} />
                  </div>
                </div>
              </div>
            )}

            {/* Modal for Broadcast Targets real-time progress list */}
            {selectedBroadcastForTargets && (
              <BroadcastTargetsModal 
                broadcastId={selectedBroadcastForTargets} 
                onClose={() => setSelectedBroadcastForTargets(null)} 
                authFetch={authFetch} 
              />
            )}
          </div>
        )}

        {/* 4. BROADCAST SYSTEM PANEL */}
        {activeTab === 'broadcast' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            
            {/* Broadcast Sender Form */}
            <div className="glass-card p-6 rounded-2xl h-fit lg:col-span-1 border border-neonViolet/20">
              <h3 className="text-lg font-bold text-white mb-6 flex items-center gap-2">
                <Send className="w-5 h-5 text-neonViolet" />
                Yangi Broadcast Yuborish
              </h3>
              
              <form onSubmit={handleSendBroadcast} className="space-y-5">
                <div>
                  <label className="text-xs text-gray-400 font-bold block mb-2 uppercase">Xabar turi</label>
                  <select
                    className="w-full bg-darkBg border border-neonViolet/20 rounded-xl px-4 py-3 text-sm text-white focus:border-neonViolet outline-none"
                    value={bcType}
                    onChange={(e) => setBcType(e.target.value)}
                  >
                    <option value="text">Text (Faqat matn)</option>
                    <option value="photo">Rasm (Photo)</option>
                    <option value="video">Video</option>
                    <option value="file">Hujjat (File)</option>
                  </select>
                </div>

                {bcType !== 'text' && (
                  <div>
                    <label className="text-xs text-gray-400 font-bold block mb-2 uppercase">Rasm/Video URL yoki Telegram File ID</label>
                    <input
                      type="text"
                      className="w-full bg-darkBg border border-neonViolet/20 rounded-xl px-4 py-3 text-sm text-white focus:border-neonViolet outline-none"
                      placeholder="https://... yoki file_id..."
                      value={bcMedia}
                      onChange={(e) => setBcMedia(e.target.value)}
                      required
                    />
                  </div>
                )}

                <div>
                  <label className="text-xs text-gray-400 font-bold block mb-2 uppercase">Matn / Xabar mazmuni</label>
                  <textarea
                    className="w-full bg-darkBg border border-neonViolet/20 rounded-xl px-4 py-3 text-sm text-white focus:border-neonViolet outline-none h-32 resize-none"
                    placeholder="HTML formatini qo'llab quvvatlaydi. Masalan: <b>Salom!</b>..."
                    value={bcText}
                    onChange={(e) => setBcText(e.target.value)}
                    required
                  />
                </div>

                <div className="border-t border-neonViolet/10 pt-4 space-y-4">
                  <span className="text-[10px] text-neonViolet font-extrabold uppercase tracking-widest">Inline Tugma Qo'shish (Ixtiyoriy)</span>
                  <div className="grid grid-cols-2 gap-3">
                    <input
                      type="text"
                      placeholder="Tugma matni"
                      className="bg-darkBg border border-neonViolet/20 rounded-xl px-3 py-2.5 text-xs text-white outline-none"
                      value={bcBtnText}
                      onChange={(e) => setBcBtnText(e.target.value)}
                    />
                    <input
                      type="text"
                      placeholder="Tugma URL manzili"
                      className="bg-darkBg border border-neonViolet/20 rounded-xl px-3 py-2.5 text-xs text-white outline-none"
                      value={bcBtnUrl}
                      onChange={(e) => setBcBtnUrl(e.target.value)}
                    />
                  </div>
                </div>

                <div className="border-t border-neonViolet/10 pt-4">
                  <label className="text-xs text-gray-400 font-bold block mb-2 uppercase flex items-center gap-1.5">
                    <Calendar className="w-4 h-4 text-neonViolet" />
                    Yuborish vaqti (Schedule) - bo'sh bo'lsa hozir ketadi
                  </label>
                  <input
                    type="datetime-local"
                    className="w-full bg-darkBg border border-neonViolet/20 rounded-xl px-4 py-2.5 text-xs text-white outline-none"
                    value={bcSchedule}
                    onChange={(e) => setBcSchedule(e.target.value)}
                  />
                </div>

                <button
                  type="submit"
                  className="w-full py-3 bg-gradient-to-r from-neonViolet to-neonPink text-white rounded-xl text-sm font-extrabold shadow-lg shadow-neonViolet/10 hover:opacity-95 transition"
                >
                  🚀 Xabarni Tarqatish
                </button>
              </form>
            </div>

            {/* Broadcast Monitor Queue */}
            <div className="glass-card p-6 rounded-2xl lg:col-span-2 space-y-6">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <Activity className="w-5 h-5 text-neonPink" />
                Yuborilgan va Navbatdagi Xabarlar
              </h3>

              <div className="space-y-4 max-h-[70vh] overflow-y-auto pr-2">
                {broadcasts.map((bc) => {
                  let progress = 0;
                  if (bc.total_targets > 0) {
                    progress = Math.round(((bc.sent_count + bc.failed_count) / bc.total_targets) * 100);
                  }
                  
                  return (
                    <div key={bc.id} className="p-4 bg-white/5 border border-white/5 rounded-2xl space-y-3 hover:bg-white/10 transition">
                      <div className="flex justify-between items-start">
                        <div>
                          <div className="flex items-center gap-2 mb-1.5">
                            <span className="text-[10px] px-2 py-0.5 bg-neonPink/20 text-neonPink border border-neonPink/30 font-bold uppercase rounded">
                              ID: {bc.id}
                            </span>
                            <span className="text-[10px] px-2 py-0.5 bg-white/10 text-gray-300 font-bold uppercase rounded">
                              {bc.type}
                            </span>
                            {bc.scheduled_at && (
                              <span className="text-[10px] text-gray-500 font-semibold">
                                Rejalashtirilgan: {new Date(bc.scheduled_at).toLocaleString('uz-UZ')}
                              </span>
                            )}
                          </div>
                          {/* Display preview of the message content */}
                          <p className="text-xs text-gray-400 line-clamp-1">{bc.content}</p>
                        </div>

                        <div className="flex items-center gap-2">
                          <span className={`px-2 py-1 rounded text-[10px] font-black uppercase ${
                            bc.status === 'sending' && 'bg-blue-600/10 text-blue-400 border border-blue-500/30'
                          } ${
                            bc.status === 'completed' && 'bg-green-600/10 text-green-400 border border-green-500/30'
                          } ${
                            bc.status === 'pending' && 'bg-yellow-600/10 text-yellow-400 border border-yellow-500/30'
                          } ${
                            bc.status === 'cancelled' && 'bg-red-600/10 text-red-400 border border-red-500/30'
                          }`}>
                            {bc.status}
                          </span>

                          <button
                            onClick={() => setSelectedBroadcastForTargets(bc.id)}
                            className="px-2.5 py-1 bg-neonViolet/10 border border-neonViolet/30 hover:bg-neonViolet text-neonViolet hover:text-white rounded text-[10px] font-extrabold uppercase transition"
                            title="Realtime yuborilganlar ro'yxati"
                          >
                            📋 Ro'yxat
                          </button>

                          {(bc.status === 'sending' || bc.status === 'pending') && (
                            <button
                              onClick={() => handleCancelBroadcast(bc.id)}
                              className="p-1 hover:bg-red-950/20 text-red-400 hover:text-red-300 border border-red-500/20 rounded transition"
                              title="Yuborishni bekor qilish"
                            >
                              <X className="w-4 h-4" />
                            </button>
                          )}
                        </div>
                      </div>

                      {/* Progress bar */}
                      {bc.status !== 'pending' && (
                        <div className="space-y-1.5 pt-2">
                          <div className="flex justify-between text-[10px] text-gray-400 font-bold">
                            <span>Progress: {progress}%</span>
                            <span className="flex gap-2">
                              <span className="text-green-400">Yuborildi: {bc.sent_count}</span>
                              <span className="text-red-400">Xatolar: {bc.failed_count}</span>
                              <span>Target: {bc.total_targets}</span>
                            </span>
                          </div>
                          
                          <div className="w-full bg-darkBg h-2.5 rounded-full overflow-hidden border border-neonViolet/10">
                            <div 
                              className={`h-full bg-gradient-to-r ${
                                bc.status === 'completed' ? 'from-green-500 to-emerald-400' : 'from-neonViolet to-neonPink'
                              }`}
                              style={{ width: `${progress}%` }}
                            ></div>
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

          </div>
        )}

      </main>
    </div>
  );
}

// Inner Component to safely fetch Quiz questions on demand
function QuizQuestionsList({ quizId, authFetch }) {
  const [questions, setQuestions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    const fetchQuestions = async () => {
      try {
        const res = await authFetch(`/api/quizzes/${quizId}`);
        if (!res.error && active) {
          const data = await res.json();
          setQuestions(data.questions || []);
        }
      } catch (e) {
        console.error(e);
      } finally {
        if (active) setLoading(false);
      }
    };
    fetchQuestions();
    return () => { active = false; };
  }, [quizId]);

  if (loading) {
    return <p className="text-sm text-gray-500 animate-pulse text-center py-6">⏳ Savollar yuklanmoqda...</p>;
  }

  return (
    <div className="space-y-4">
      {questions.map((q, idx) => (
        <div key={q.id} className="p-4 bg-white/5 border border-white/5 rounded-xl space-y-3">
          <p className="text-sm font-semibold text-white">🙋‍♂️ {idx + 1}-savol: {q.question_text}</p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2 pl-4">
            {q.options.map((opt, oIdx) => (
              <div key={oIdx} className="text-xs p-2 rounded-lg bg-darkBg border border-white/5 flex items-center justify-between">
                <span>{opt}</span>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function BroadcastTargetsModal({ broadcastId, onClose, authFetch }) {
  const [targets, setTargets] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchTargets = async () => {
    try {
      const res = await authFetch(`/api/broadcast/${broadcastId}/targets`);
      if (!res.error) {
        const data = await res.json();
        setTargets(data || []);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTargets();
    const interval = setInterval(fetchTargets, 3000);
    return () => clearInterval(interval);
  }, [broadcastId]);

  const formatTashkentTime = (utcString) => {
    if (!utcString) return "Navbatda...";
    const date = new Date(utcString);
    const tzDate = new Date(date.getTime() + (5 * 60 * 60 * 1000));
    return tzDate.toISOString().replace('T', ' ').substring(0, 19);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-6 backdrop-blur-sm">
      <div className="glass-card w-full max-w-3xl rounded-2xl overflow-hidden border border-neonViolet/30 flex flex-col max-h-[85vh]">
        <header className="flex justify-between items-center p-6 border-b border-neonViolet/10 bg-white/5">
          <div>
            <span className="text-xs text-neonViolet font-bold tracking-widest uppercase">Real-Time Progress</span>
            <h3 className="text-xl font-extrabold text-white leading-tight">Yuborilish Tafsilotlari (ID: {broadcastId})</h3>
          </div>
          <button 
            onClick={onClose}
            className="p-2 hover:bg-white/5 rounded-full text-gray-400 hover:text-white"
          >
            <X className="w-5 h-5" />
          </button>
        </header>
        
        <div className="p-6 overflow-y-auto flex-1 bg-darkBg/95">
          {loading ? (
            <p className="text-sm text-gray-500 animate-pulse text-center py-6">⏳ Ma'lumotlar yuklanmoqda...</p>
          ) : targets.length === 0 ? (
            <p className="text-sm text-gray-500 text-center py-6">Ushbu xabar uchun hech qanday target topilmadi.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-neonViolet/10 text-gray-400 text-xs uppercase bg-white/5">
                    <th className="py-3 px-4">Foydalanuvchi</th>
                    <th className="py-3 px-4 text-center">Status</th>
                    <th className="py-3 px-4 text-center">Toshkent Vaqti</th>
                    <th className="py-3 px-4 text-right">Xatolik</th>
                  </tr>
                </thead>
                <tbody>
                  {targets.map((t) => (
                    <tr key={t.id} className="border-b border-neonViolet/5 text-sm hover:bg-white/5 transition">
                      <td className="py-3 px-4">
                        <p className="font-semibold text-white">{t.first_name || 'Ismsiz'}</p>
                        <span className="text-xs text-neonViolet">@{t.username || t.user_id}</span>
                      </td>
                      <td className="py-3 px-4 text-center">
                        <span className={`px-2.5 py-0.5 rounded text-[10px] font-black uppercase ${
                          t.status === 'sent' && 'bg-green-500/10 text-green-400 border border-green-500/30'
                        } ${
                          t.status === 'failed' && 'bg-red-500/10 text-red-400 border border-red-500/30'
                        } ${
                          t.status === 'pending' && 'bg-yellow-500/10 text-yellow-400 border border-yellow-500/30'
                        }`}>
                          {t.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-center text-xs text-gray-400 font-mono">
                        {formatTashkentTime(t.sent_at)}
                      </td>
                      <td className="py-3 px-4 text-right text-xs text-red-400 max-w-[200px] truncate" title={t.error_message}>
                        {t.error_message || "-"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
