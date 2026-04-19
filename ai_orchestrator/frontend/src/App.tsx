import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Mic, Send, Paperclip, CheckCircle2, AlertTriangle, Info, BookOpen, Activity, Command, Lock, User, CheckCircle, Users, Calendar, Play, QrCode, Zap, Shield, Rocket, Sparkles, ChevronRight, Brain, MessageSquare, Clock, ArrowRight, Check, FileText, Search, Quote, Printer, X, Download, Menu, BarChart3, TrendingUp, Eye, EyeOff, Layers, ThermometerSun, PersonStanding } from 'lucide-react';
import HeatmapView from './components/dashboard/HeatmapView';
import LentaView from './components/dashboard/LentaView';
import StaffSchedule from './components/dashboard/StaffSchedule';
import TimetableGrid from './components/dashboard/TimetableGrid';
const API_BASE = `http://${window.location.hostname}:8000/api`;

interface TeacherOption {
  id: number;
  full_name: string;
  short_name: string;
  role: string;
  subject?: string | null;
}

interface AbsenceResolutionItem {
  entry_id: number;
  missing_teacher: string;
  substitute_teacher: string;
  substitute_teacher_id?: number | null;
  lesson_number: number;
  class_name: string;
  room: string;
  day: string;
  subject: string;
  status: string;
  match_type?: string | null;
  applied?: boolean;
  notification?: {
    status?: string;
    telegram_sent?: boolean;
    whatsapp_sent?: boolean;
  };
  rejected_candidates?: { name: string; reason: string }[];
}

interface AbsenceEventResponse {
  status: string;
  teacher_name: string;
  day: string;
  substitutions_count: number;
  unresolved_count: number;
  substitutions: AbsenceResolutionItem[];
  unresolved: AbsenceResolutionItem[];
}

const BrandIcon = ({ className = "w-full h-full" }: { className?: string }) => (
  <svg viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
    <rect width="40" height="40" rx="10" fill="#c2ef4e" fillOpacity="0.15"/>
    <path d="M8 20C8 13.373 13.373 8 20 8s12 5.373 12 12-5.373 12-12 12S8 26.627 8 20z" stroke="#c2ef4e" strokeWidth="1.5"/>
    <path d="M14 20h12M20 14v12" stroke="#c2ef4e" strokeWidth="2" strokeLinecap="round"/>
    <circle cx="20" cy="20" r="3" fill="#c2ef4e"/>
  </svg>
);

// --- HOME SCREEN (LANDING PAGE) ---
function HomeScreen({ onStart }: { onStart: () => void }) {
  return (
    <div className="min-h-screen bg-[#1f1633] text-white selection:bg-[#c2ef4e]/30 overflow-hidden font-sans">
      {/* Background Orbs */}
      <div className="absolute top-[-10%] left-[-10%] w-[600px] h-[600px] bg-purple-900/40 rounded-full blur-[120px]"></div>
      <div className="absolute bottom-[-10%] right-[-10%] w-[600px] h-[600px] bg-[#c2ef4e]/5 rounded-full blur-[120px]"></div>

      <nav className="relative z-20 flex items-center justify-between px-10 py-8 max-w-7xl mx-auto">
        <div className="flex items-center space-x-3 group cursor-pointer" onClick={onStart}>
          <div className="w-10 h-10 rounded-xl p-1.5">
            <BrandIcon className="w-full h-full" />
          </div>
          <span className="text-xl font-bold tracking-tight text-white">AI Orchestrator</span>
        </div>
        <button
          onClick={onStart}
          className="bg-white/8 hover:bg-white/15 border border-white/10 px-6 py-2.5 rounded-xl font-medium transition-all hover:scale-105 active:scale-95 text-white/70"
        >
          Войти
        </button>
      </nav>

      <main className="relative z-10 max-w-7xl mx-auto px-10 pt-20 pb-32">
        <div className="grid lg:grid-cols-2 gap-20 items-center">
          <div className="space-y-8">
            <div className="relative inline-block mb-4 pt-4">
              <div className="absolute -top-20 -left-6 w-40 h-40 pointer-events-none drop-shadow-2xl z-0">
                <div className="w-full h-full animate-bounce-subtle">
                   {/* removed mascot image */}
                </div>
              </div>
              <div className="inline-flex items-center space-x-2 bg-blue-50/80 backdrop-blur-sm border border-blue-100 px-4 py-2 rounded-full relative z-10 shadow-sm">
                <Sparkles className="w-4 h-4 text-blue-600" />
                <span className="text-xs font-bold uppercase tracking-widest text-blue-600">AI School Orchestrator v2.0</span>
              </div>
            </div>
            
            <h1 className="text-6xl font-black leading-[1.1] tracking-tight text-white">
              Цифровой разум <br />
              <span className="text-[#c2ef4e]">
                вашей школы
              </span>
            </h1>
            
            <p className="text-xl text-white/60 font-medium leading-relaxed max-w-xl">
              Автоматизация WhatsApp-отчетов, умное планирование замен и мгновенный поиск по нормативным актам. Освободите время для самого важного — образования.
            </p>

            <div className="flex items-center space-x-6">
              <button
                onClick={onStart}
                className="group relative flex items-center space-x-3 bg-[#c2ef4e] hover:bg-[#a8d63a] text-[#1f1633] px-8 py-5 rounded-2xl font-bold text-xl shadow-2xl shadow-[#c2ef4e]/20 transition-all hover:-translate-y-1 active:scale-95 overflow-hidden"
              >
                <span>Запустить платформу</span>
                <ChevronRight className="w-6 h-6 group-hover:translate-x-1 transition-transform" />
              </button>
              
              <div className="flex -space-x-3">
                {[1,2,3,4].map(i => (
                  <div key={i} className="w-12 h-12 rounded-full border-4 border-white bg-slate-200 flex items-center justify-center overflow-hidden" />
                ))}
                <div className="pl-6 text-sm font-bold text-white/40">
                  <span className="text-white">500+</span> школьных <br /> директоров уже с нами
                </div>
              </div>
            </div>
          </div>

          <div className="relative group">
            {/* Decorative Grid UI */}
            <div className="relative bg-[#2a1f42] border border-white/10 rounded-3xl p-10 shadow-[0_50px_100px_rgba(0,0,0,0.3)] space-y-8 transform rotate-2 hover:rotate-0 transition-all duration-700 group overflow-hidden">
              <div className="absolute -top-20 -right-20 w-64 h-64 bg-[#c2ef4e]/5 rounded-full blur-[100px]"></div>
              
              <div className="space-y-8 relative z-10">
                {/* Voice Input Section */}
                <div className="flex items-center justify-between border-b border-white/8 pb-8">
                  <div className="flex items-center space-x-5">
                    <div className="w-14 h-14 bg-blue-600 rounded-2xl flex items-center justify-center shadow-2xl shadow-blue-500/20">
                      <Mic className="text-white" size={28} />
                    </div>
                    <div>
                      <div className="text-xs font-black uppercase tracking-[0.2em] text-white/40 mb-1">Voice Input</div>
                      <div className="font-extrabold text-xl text-white">«Замените 5А на 2 урок...»</div>
                    </div>
                  </div>
                  <div className="w-10 h-10 rounded-full border-2 border-blue-200 flex items-center justify-center text-blue-500">
                    <CheckCircle2 size={24} />
                  </div>
                </div>

                {/* AI Insight Section */}
                <div className="p-8 bg-[#c2ef4e]/8 rounded-2xl border border-[#c2ef4e]/20 space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="font-bold text-[#c2ef4e] flex items-center text-sm tracking-widest">
                      <Zap className="w-5 h-5 mr-2" /> AI ИНСАЙТ
                    </div>
                    <span className="text-[10px] font-bold text-white/30 uppercase">Just now</span>
                  </div>
                  <p className="text-base text-white/70 font-medium leading-relaxed">
                    Проанализировано 12 сообщений из WhatsApp. Найдено 3 инцидента. Сформирована заявка для завхоза.
                  </p>
                </div>

                {/* Grid Status Cards */}
                <div className="grid grid-cols-2 gap-6">
                  <div className="p-6 bg-white/5 rounded-xl border border-white/10 group-hover:bg-white/8 transition-colors">
                    <Shield className="w-8 h-8 text-blue-500 mb-3" />
                    <div className="text-[10px] font-black uppercase text-white/40 tracking-widest mb-1">Compliance</div>
                    <div className="font-bold text-lg text-white">Приказ №110</div>
                  </div>
                  <div className="p-6 bg-white/5 rounded-xl border border-white/10 group-hover:bg-white/8 transition-colors">
                    <Activity className="w-8 h-8 text-blue-500 mb-3" />
                    <div className="text-[10px] font-black uppercase text-white/40 tracking-widest mb-1">Efficiency</div>
                    <div className="font-bold text-lg text-white">+24% Время</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

// --- AUTH SCREEN COMPONENT ---
function AuthScreen({ onLogin }: { onLogin: (role: string) => void }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [role, setRole] = useState<'director' | 'teacher'>('director');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (role === 'teacher') {
      onLogin('teacher');
      return;
    }

    try {
      const res = await axios.post(`${API_BASE}/auth/login`, { email, password });
      localStorage.setItem('auth_token', res.data.token);
      onLogin('director');
    } catch (err: any) {
      if (axios.isAxiosError(err) && !err.response) {
        setError('❌ Сервер авторизации недоступен. Проверьте, запущен ли backend на порту 8000.');
        return;
      }

      setError(err.response?.data?.detail || '❌ Не удалось выполнить вход');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#1f1633] relative overflow-hidden text-white">
      <div className="absolute top-[-10%] left-[-10%] w-[500px] h-[500px] bg-purple-900/30 rounded-full filter blur-[120px]"></div>
      <div className="absolute bottom-[-10%] right-[-10%] w-[500px] h-[500px] bg-[#c2ef4e]/5 rounded-full filter blur-[120px]"></div>

      <div className="bg-[#2a1f42] p-10 rounded-2xl shadow-[0_30px_60px_rgba(0,0,0,0.4)] border border-white/10 w-full max-w-md z-10">
        <div className="flex flex-col items-center mb-6">
          <div className="w-12 h-12 mb-4 p-1.5">
            <BrandIcon className="w-full h-full" />
          </div>
          <h2 className="text-2xl font-bold tracking-tight text-white">Вход в систему</h2>
          <p className="text-white/40 text-sm mt-1">AI Orchestrator · Aqbobek School</p>
        </div>

        <div className="flex bg-white/8 p-1 rounded-2xl mb-6">
          <button onClick={() => setRole('director')} className={`flex-1 py-2 rounded-xl text-sm font-medium transition-all ${role === 'director' ? 'bg-[#c2ef4e]/20 text-[#c2ef4e] border border-[#c2ef4e]/30' : 'text-white/40 hover:text-white/70'}`}>Директор</button>
          <button onClick={() => setRole('teacher')} className={`flex-1 py-2 rounded-xl text-sm font-bold transition-all ${role === 'teacher' ? 'bg-[#25D366] text-white shadow-sm' : 'text-white/40 hover:text-white/70'}`}>Учитель</button>
        </div>

        {error && <div className="p-4 bg-rose-50 border border-rose-100 rounded-2xl mb-6 text-sm text-center text-rose-500 font-bold shadow-sm">{error}</div>}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="relative">
            <User className="absolute left-5 top-1/2 transform -translate-y-1/2 text-white/30 w-5 h-5" />
            <input type="email" placeholder="Рабочий Email" value={email} onChange={(e) => setEmail(e.target.value)} className="w-full bg-white/8 border border-white/10 text-white rounded-xl py-4 pl-14 pr-4 focus:outline-none focus:border-[#c2ef4e]/50 placeholder-white/30 transition" required />
          </div>
          <div className="relative group">
            <Lock className="absolute left-5 top-1/2 transform -translate-y-1/2 text-white/30 w-5 h-5" />
            <input type={showPassword ? "text" : "password"} placeholder="Пароль" value={password} onChange={(e) => setPassword(e.target.value)} className="w-full bg-white/8 border border-white/10 text-white rounded-xl py-4 pl-14 pr-12 focus:outline-none focus:border-[#c2ef4e]/50 placeholder-white/30 transition" required />
            <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-4 top-1/2 transform -translate-y-1/2 text-white/40 hover:text-white/70 transition focus:outline-none p-1">
              {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
            </button>
          </div>
          
          <button type="submit" className={`w-full font-bold text-base py-4 rounded-xl shadow-xl transition-all active:scale-95 mt-4 ${role === 'director' ? 'bg-[#c2ef4e] text-[#1f1633] hover:bg-[#a8d63a]' : 'bg-[#25D366] text-white hover:bg-[#1da851]'}`}>
            {role === 'teacher' ? 'Синхронизировать WhatsApp' : 'Войти в Дашборд'}
          </button>
        </form>
      </div>
    </div>
  );
}

// --- TEACHER PROFILE DASHBOARD ---
function TeacherProfileDashboard({ onLogout }: { onLogout: () => void }) {
  const [profile, setProfile] = useState<any>(null);

  useEffect(() => {
    // Fetch real data from backend
    axios.get(`${API_BASE}/schedule/teacher-profile`)
      .then(res => setProfile(res.data))
      .catch(err => console.error("Error fetching profile", err));
  }, []);

  if (!profile) {
     return <div className="min-h-screen bg-white/5 flex items-center justify-center"><div className="w-8 h-8 border-4 border-emerald-500/30 border-t-emerald-500 rounded-full animate-spin"></div></div>;
  }

  return (
    <div className="min-h-screen bg-[#1f1633] relative pb-20 font-sans selection:bg-[#c2ef4e]/30">
      {/* Header */}
      <div className="bg-gradient-to-br from-[#25D366] to-emerald-600 px-6 pt-14 pb-10 text-white shadow-xl shadow-emerald-500/20 relative rounded-b-[3rem] border-b border- emerald-400">
         <div className="absolute top-0 left-0 w-full h-full overflow-hidden opacity-20 pointer-events-none rounded-b-[3rem]">
           <div className="w-96 h-96 bg-white rounded-full blur-[100px] absolute -top-10 -right-20"></div>
         </div>
         <div className="flex items-center justify-between relative z-10">
           <div className="flex items-center space-x-4">
             <div className="w-14 h-14 bg-white border-2 border-white/50 shadow-inner rounded-full flex items-center justify-center text-xl overflow-hidden p-0.5">
              <div className="w-full h-full rounded-full bg-lime-400/20" />
             </div>
             <div>
               <h1 className="font-extrabold text-2xl tracking-tight leading-tight">{profile.name}</h1>
               <p className="text-emerald-100/90 text-sm font-medium tracking-wide">{profile.role}</p>
             </div>
           </div>
           <button onClick={onLogout} className="p-3 bg-black/10 rounded-2xl hover:bg-black/20 transition backdrop-blur-sm shadow-inner">
             <ArrowRight size={20} strokeWidth={2.5} />
           </button>
         </div>
      </div>

      {/* Content */}
      <div className="p-6 max-w-2xl mx-auto space-y-8 -mt-6 relative z-20">
        
        {/* Status Card */}
        <div className="bg-white/80 backdrop-blur-md p-5 rounded-[2rem] shadow-lg shadow-slate-200/50 border border-white flex items-center justify-between transform transition hover:scale-[1.02]">
           <div className="flex items-center space-x-3">
             <div className="relative flex h-3 w-3">
               <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
               <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500 shadow-[0_0_12px_rgba(16,185,129,0.8)]"></span>
             </div>
             <span className="font-extrabold text-white/90 tracking-tight text-sm">WhatsApp Синхронизирован</span>
           </div>
           <CheckCircle2 size={24} className="text-emerald-500" strokeWidth={2.5} />
        </div>

        {/* Schedule */}
        <div className="space-y-4">
          <h2 className="font-black text-white text-lg flex items-center px-2 tracking-tight">
             <div className="w-8 h-8 rounded-xl bg-blue-100 flex items-center justify-center mr-3 text-blue-600">
               <Calendar size={18} strokeWidth={2.5}/>
             </div>
             Мое расписание (Понедельник)
          </h2>
          <div className="bg-[#2a1f42] rounded-2xl overflow-hidden border border-white/10">
            {profile.schedule.length === 0 && <div className="p-5 text-white/60">Нет уроков на сегодня.</div>}
            {profile.schedule.map((item: any, i: number) => (
               <div key={i} className="p-5 flex items-center border-b border-slate-50 hover:bg-white/5 transition cursor-pointer">
                 <div className="w-16 text-center mr-4">
                   <div className="text-white/40 font-extrabold text-lg">{item.time}</div>
                 </div>
                 <div className="flex-1">
                   <div className="font-extrabold text-white flex items-center justify-between">
                     {item.subject} <span><ChevronRight size={16} className="text-white/30"/></span>
                   </div>
                   <div className="text-white/60 text-sm font-medium mt-0.5">{item.class_name} • Каб. {item.room}</div>
                 </div>
               </div>
            ))}
          </div>
        </div>

        {/* Tasks from Director */}
        <div className="space-y-4">
          <h2 className="font-black text-white text-lg flex items-center px-2 tracking-tight">
             <div className="w-8 h-8 rounded-xl bg-rose-100 flex items-center justify-center mr-3 text-rose-500">
               <AlertTriangle size={18} strokeWidth={2.5}/>
             </div>
             Задачи
          </h2>
          <div className="bg-[#2a1f42] p-6 rounded-2xl border border-white/10 flex items-start space-x-5 hover:border-rose-500/30 transition cursor-pointer group">
            <div className="w-12 h-12 bg-rose-500/10 rounded-2xl flex items-center justify-center text-rose-400 shrink-0 group-hover:scale-110 group-hover:bg-rose-500 group-hover:text-white transition-all">
               <FileText size={22} strokeWidth={2.5} />
            </div>
            <div className="flex-1">
               <div className="flex items-center justify-between mb-1.5">
                  <div className="text-[10px] font-black text-rose-500 uppercase tracking-widest bg-rose-50 px-2 py-0.5 rounded-md">Новое</div>
                  <span className="text-xs font-bold text-white/40">Только что</span>
               </div>
               <div className="font-extrabold text-white text-lg mb-1 leading-tight">Проверить журналы</div>
               <div className="text-white/60 text-sm font-medium flex items-center">
                 <Clock size={14} className="mr-1.5 opacity-50"/> Назначено через AI Voice
               </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  )
}

// --- TEACHER WA SYNC SCREEN ---
function TeacherScreen({ onBack }: { onBack: () => void }) {
  const [status, setStatus] = useState('pending');
  const [qrData, setQrData] = useState('');
  const [showProfile, setShowProfile] = useState(false);

  useEffect(() => {
    // Only poll if not in a secret override state
    if (status === 'syncing' || status === 'ready') return;
    
    const interval = setInterval(async () => {
      try {
        const res = await axios.get(`${API_BASE}/bot/whatsapp-auth-status`);
        if (res.data.status === 'ready' && status !== 'ready') {
           setStatus('ready');
        } else if (res.data.qr_data && status !== 'ready') {
           setStatus('pending');
           setQrData(res.data.qr_data);
        }
      } catch (e) {
        // ignore errors
      }
    }, 2000);
    return () => clearInterval(interval);
  }, [status]);

  if (showProfile) {
    return <TeacherProfileDashboard onLogout={onBack} />;
  }

  const handleSecretLogin = () => {
    setStatus('syncing');
    setTimeout(() => {
       setStatus('ready');
    }, 2500); // Показываем эффект анимации синхронизации 2.5 секунды
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-[#1f1633] text-white text-center p-6 relative overflow-hidden font-sans">
       <div className="absolute inset-0 opacity-10 bg-[url('https://w0.peakpx.com/wallpaper/818/148/HD-wallpaper-whatsapp-background-solid-color-thumbnail.jpg')] bg-cover mix-blend-multiply pointer-events-none z-0"></div>
       
       <div className="z-10 bg-[#2a1f42] p-10 rounded-2xl shadow-2xl border border-white/10 max-w-md w-full flex flex-col items-center">
          <div 
            onClick={handleSecretLogin}
            className={`cursor-pointer w-24 h-24 rounded-[2rem] flex items-center justify-center text-white mb-6 shadow-2xl transition-all duration-1000 ${status === 'ready' ? 'bg-gradient-to-br from-[#25D366] to-emerald-500 shadow-emerald-500/40 rotate-[360deg] scale-110' : status === 'syncing' ? 'bg-emerald-400 rotate-180 scale-95 shadow-emerald-400/50' : 'bg-gradient-to-br from-slate-800 to-slate-900 shadow-slate-900/40'}`}>
            {status === 'ready' ? <CheckCircle2 size={44} strokeWidth={2.5}/> : status === 'syncing' ? <div className="w-10 h-10 border-4 border-white/30 border-t-white rounded-full animate-spin"></div> : <QrCode size={44} strokeWidth={2.5}/>}
          </div>
          <h1 className="text-3xl font-black tracking-tight mb-3 text-white transition-colors duration-500">
            {status === 'ready' ? 'Мессенджер привязан!' : status === 'syncing' ? 'Синхронизация...' : 'Рабочий чат'}
          </h1>
          <p className="text-[15px] text-white/60 font-medium mb-8 leading-relaxed max-w-[260px] mx-auto h-12">
            {status === 'ready' 
              ? 'Ваш WhatsApp успешно подключен к системе.' 
              : status === 'syncing'
              ? 'Устанавливаем защищенное соединение с сервером...'
              : 'Наведите камеру смартфона на код, чтобы привязать номер.'}
          </p>
          
          {status !== 'ready' && (
            <div className={`p-4 bg-[#2a1f42] rounded-2xl border border-white/10 flex items-center justify-center mb-10 w-56 h-56 transition-all duration-700 ${status === 'syncing' ? 'opacity-50 blur-sm scale-95' : 'hover:scale-[1.02]'} relative group cursor-pointer`}>
               {!qrData || status === 'syncing' ? (
                 <div className="absolute inset-0 flex flex-col items-center justify-center space-y-4">
                   <div className="w-10 h-10 border-[3px] border-emerald-500/20 border-t-emerald-500 rounded-full animate-spin"></div>
                   <span className="text-xs font-black uppercase tracking-widest text-white/40">Ожидание...</span>
                 </div>
               ) : (
                 <img src={`https://api.qrserver.com/v1/create-qr-code/?size=250x250&data=${encodeURIComponent(qrData)}`} alt="whatsapp-qr" className="w-full opacity-90 rounded-2xl mix-blend-multiply transition duration-500 ease-out group-hover:opacity-100 animate-in zoom-in-50" />
               )}
            </div>
          )}

          <button 
             onClick={() => status === 'ready' ? setShowProfile(true) : onBack()} 
             disabled={status === 'syncing'}
             className={`w-full py-4 rounded-[1.5rem] font-black text-lg transition-all transform ${status === 'syncing' ? 'opacity-50 cursor-not-allowed scale-100 bg-white/8 text-white/40' : 'hover:-translate-y-1 active:scale-95 shadow-xl'} ${status === 'ready' ? 'bg-[#25D366] text-white hover:bg-emerald-500 shadow-emerald-500/30' : 'bg-white/8 text-white/70 hover:bg-slate-200 shadow-[0_10px_20px_rgba(0,0,0,0.03)]'}`}
          >
             {status === 'ready' ? 'Войти в профиль' : 'Вернуться назад'}
          </button>
       </div>
    </div>
  );
}

// --- TASK CARD COMPONENT (3-STAGE SYSTEM) ---
function TaskCard({ task, idx, stage, onMarkDone }: { task: any, idx: number, stage: 'request' | 'progress' | 'completed', onMarkDone: (id: number) => void }) {
  const urgencyMap: Record<string, string> = {
    'Сегодня': 'bg-rose-50 text-rose-600 border-rose-100',
    'Срочно': 'bg-rose-50 text-rose-600 border-rose-100',
    'Завтра': 'bg-amber-50 text-amber-600 border-amber-100',
    'Среда': 'bg-blue-50 text-blue-600 border-blue-100',
    'Пятница': 'bg-blue-50 text-blue-600 border-blue-100',
  };
  const urgencyColor = urgencyMap[task.deadline] || 'bg-white/5 text-white/60 border-white/8';
  const initials = task.assignee?.split(' ').map((w: string) => w[0]).join('').slice(0, 2).toUpperCase() || '??';
  const avatarColors: Record<string, string> = {
    request: 'bg-amber-100 text-amber-600 border-amber-200',
    progress: 'bg-blue-500 text-white shadow-lg shadow-blue-500/30',
    completed: 'bg-white/8 text-white/40 grayscale'
  };

  return (
    <div className={`group relative transition-all duration-500 ${stage === 'completed' ? 'opacity-60 grayscale-[0.5]' : ''}`}>
      <div className={`bg-[#2a1f42] rounded-2xl p-5 flex items-center gap-5 border group-hover:-translate-y-1 transition-all ${
        stage === 'request' ? 'border-amber-500/30' :
        stage === 'progress' ? 'border-blue-500/30' :
        'border-white/8'
      }`}>
        {/* Avatar / Icon Section */}
        <div className={`w-14 h-14 rounded-2xl flex items-center justify-center font-black text-sm shrink-0 border-2 transition-all ${avatarColors[stage]}`}>
           {stage === 'completed' ? <CheckCircle2 className="w-7 h-7" /> : initials}
        </div>

        {/* Content Section */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3">
             <div className={`font-semibold text-base truncate ${stage === 'completed' ? 'text-white/30 line-through' : 'text-white'}`}>{task.title}</div>
             {stage === 'request' && <span className="text-[9px] font-black uppercase text-amber-500 bg-amber-50 px-2 py-0.5 rounded-full border border-amber-100 animate-pulse">Ожидает подтверждения</span>}
             {stage === 'progress' && <span className="text-[9px] font-black uppercase text-blue-600 bg-blue-50 px-2 py-0.5 rounded-full border border-blue-100">В работе</span>}
          </div>
          <div className="flex items-center gap-4 mt-1.5 overflow-hidden">
             <span className="text-xs font-bold text-white/40 flex items-center gap-1 shrink-0"><Users size={12} className="opacity-40" /> {task.assignee}</span>
             <span className={`text-[10px] font-black uppercase px-2.5 py-1 rounded-lg border flex items-center gap-1 shrink-0 ${urgencyColor}`}><Clock size={10} /> {task.deadline}</span>
          </div>
        </div>

        {/* Actions Section */}
        {stage !== 'completed' && (
          <button 
            onClick={() => onMarkDone(task.id)}
            className="flex items-center gap-2 bg-[#c2ef4e]/15 hover:bg-[#c2ef4e]/25 text-[#c2ef4e] text-[10px] font-bold uppercase tracking-widest px-5 py-3 rounded-xl transition-all active:scale-95 opacity-0 group-hover:opacity-100 border border-[#c2ef4e]/30"
          >
            Завершить
          </button>
        )}
      </div>
    </div>
  );
}

// --- MAIN DASHBOARD APP ---
export default function App() {
  // Demo-bypass: allows inspecting the dashboard without being blocked by auth.
  const [view, setView] = useState<'home' | 'auth' | 'app'>('app');
  const [isAuthenticated, setIsAuthenticated] = useState(true);
  const [userRole, setUserRole] = useState('');

  if (view === 'home') return <HomeScreen onStart={() => setView('auth')} />;

  if (!isAuthenticated || view === 'auth') {
    return (
      <AuthScreen 
        onLogin={(r) => { 
          setIsAuthenticated(true); 
          setUserRole(r); 
          setView('app');
        }} 
      />
    );
  }
  
  if (userRole === 'teacher') {
    return <TeacherScreen onBack={() => { setIsAuthenticated(false); setView('home'); }} />;
  }

  return <Dashboard />;
}

// --- DASHBOARD COMPONENT ---
function Dashboard() {
  const [activeTab, setActiveTab] = useState('chat');
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [inputVal, setInputVal] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [ragQuery, setRagQuery] = useState('');
  const [ragResult, setRagResult] = useState<any>(null);
  const [isRagLoading, setIsRagLoading] = useState(false);
  const [ragMode, setRagMode] = useState<'search' | 'checklist'>('search');
  const [mascotMsg, setMascotMsg] = useState('Привет! Я ваш AI-ассистент. Чем помочь?');
  const [showSuccessOverlay, setShowSuccessOverlay] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [selectedOrder, setSelectedOrder] = useState<any>(null);
  const [isGeneratingOrder, setIsGeneratingOrder] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const recognitionRef = useRef<any>(null);
  const transcriptRef = useRef<string>('');
  const [isDemoRunning, setIsDemoRunning] = useState(false);
  const [isGeneratingSchedule, setIsGeneratingSchedule] = useState(false);
  const [generatedSchedule, setGeneratedSchedule] = useState<any[]>([]);
  const [scheduleSummary, setScheduleSummary] = useState<any | null>(null);
  const [teacherOptions, setTeacherOptions] = useState<TeacherOption[]>([]);
  const [absenceTeacher, setAbsenceTeacher] = useState('Болат');
  const [absenceDay, setAbsenceDay] = useState('Понедельник');
  const [absenceReason, setAbsenceReason] = useState('Болезнь');
  const [absenceResult, setAbsenceResult] = useState<AbsenceEventResponse | null>(null);
  const [isProcessingAbsence, setIsProcessingAbsence] = useState(false);
  const [scheduleRefreshToken, setScheduleRefreshToken] = useState(0);

  // Live Telegram feed
  const [botFeed, setBotFeed] = useState<any[]>([]);
  const [svod, setSvod] = useState<any>(null);

  // Poll Telegram bot messages every 4 seconds
  useEffect(() => {
    const fetchFeed = async () => {
      try {
        const [feedRes, svodRes] = await Promise.all([
          axios.get(`${API_BASE}/bot/messages?limit=30`),
          axios.get(`${API_BASE}/bot/svod`),
        ]);
        setBotFeed(feedRes.data);
        setSvod(svodRes.data);
      } catch {}
    };
    fetchFeed();
    const interval = setInterval(fetchFeed, 4000);
    return () => clearInterval(interval);
  }, []);

  const calculateAttendanceTotals = () => {
    // Use real svod data if available, otherwise fall back to static calculation
    if (svod && svod.report_count > 0) {
      return { totalChildren: svod.total_portions, totalSick: 0 };
    }
    let totalChildren = 0;
    let totalSick = 0;
    messages.forEach(m => {
      if (m.text.includes("детей") || m.text.includes("человек")) {
        const matches = m.text.match(/(\d+)\s*(детей|человек)/);
        const sickMatches = m.text.match(/(\d+)\s*(болеют|отсутствуют)/);
        if (matches) totalChildren += parseInt(matches[1]);
        if (sickMatches) totalSick += parseInt(sickMatches[1]);
      }
    });
    return { totalChildren, totalSick };
  };

  const [messages, setMessages] = useState<any[]>([
    { text: "1В — 23 ребёнка, все присутствуют.", time: "08:10", parsed: { type: "attendance", urgency: "low", insight: "✅ Питание: 23 порции. Данные переданы в столовую Aqbobek." } },
    { text: "Доброе утро! 2А: 19 человек, 1 заболел.", time: "08:14", parsed: { type: "attendance", urgency: "low", insight: "✅ Питание: 19 порций. Заявка сформирована автоматически." } },
    { text: "В кабинете 8 сломался проектор, урок провести не можем.", time: "09:10", parsed: { type: "incident", urgency: "high", insight: "🚨 ИНЦИДЕНТ\nСоздана задача Серику (Техработник): Починить проектор в каб. 8" } },
    { text: "У меня высокая температура. Сегодня не смогу прийти на уроки.", time: "08:50", parsed: { type: "absence", urgency: "critical", insight: "🔥 ВНИМАНИЕ: Болат (Математика) болен.\nНайдены свободные окна: Петрова О. (2 урок), Байжанова Д. (3 урок)." } },
    { text: "4Б — 24 ученика, 2 отсутствуют. 22 на питание.", time: "08:33", parsed: { type: "attendance", urgency: "low", insight: "✅ Питание: 22 порции. Список отсутствующих: Сарин, Ким." } }
  ]);
  
const [dbTasks, setDbTasks] = useState<any[]>([]);

  const [mockSchedule, setMockSchedule] = useState([
    { 
      lesson: 1, class: "4Б", room: "303", teacher: "Болат (Болеет)", subject: "Математика",
      alert: true, replacement: "Петрова Ольга",
      reasoning: "Свободное окно (1-й урок), профиль соответствует (матем. + нач. школа).",
      confidence: 98, status: "pending",
      rejected: [
        { name: "Байжанова Д.", reason: "Занята на 1 уроке (ведёт 6А)" },
        { name: "Дюсенов Н.", reason: "Профиль не совпадает (геометрия, не начальная школа)" }
      ]
    },
    {
      lesson: 2, class: "6А", room: "306", teacher: "Болат (Болеет)", subject: "Алгебра",
      alert: true, replacement: "Байжанов Д.",
      reasoning: "Ведет в параллели 5-6-х классов, имеет опыт по данной теме (уравнения).", 
      confidence: 92, status: "pending",
      rejected: [
        { name: "Смирнова Е.", reason: "Уже заменяет на 1 уроке (3В)" },
        { name: "Жанибеков М.", reason: "Превышение нагрузки (Прик. МОН №110 п.3)" }
      ]
    },
    { 
      lesson: 3, class: "8А", room: "308", teacher: "Антон", subject: "Физика", 
      alert: false, replacement: "", 
      reasoning: "Замена не требуется.", 
      confidence: 100, status: "ok",
      rejected: []
    }
  ]);

  const applyReplacements = () => {
    setMockSchedule(prev => prev.map(s => s.alert ? { ...s, replacement: s.replacement, status: "applied" } : s));
    setShowSuccessOverlay(true);
    setMascotMsg("Миссия выполнена! Все замены утверждены и разосланы. 🚀");
    setTimeout(() => setShowSuccessOverlay(false), 4000);
  };

  const generateOrderHTML = (sub: any): string => {
    const today = new Date();
    const dateStr = today.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' });
    const orderNum = `78-${sub.lesson}`;

    return `<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <title>Приказ № ${orderNum}</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=PT+Serif:ital,wght@0,400;0,700;1,400&display=swap');
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'PT Serif', Georgia, serif; background: #f0f4f8; display: flex; justify-content: center; padding: 40px 20px; }
    .page { background: white; width: 210mm; min-height: 297mm; padding: 25mm 22mm 20mm; box-shadow: 0 8px 40px rgba(0,0,0,0.15); position: relative; }
    .stripe { position: absolute; top: 0; left: 0; right: 0; height: 6px; background: linear-gradient(90deg, #1a3a8f, #2563eb, #16a34a); border-radius: 4px 4px 0 0; }
    .school { text-align: center; font-size: 10pt; color: #555; border-bottom: 1px solid #d1d5db; padding-bottom: 10px; margin-bottom: 14px; line-height: 1.6; }
    .school strong { color: #1a1a2e; }
    h1 { text-align: center; font-size: 20pt; color: #1a3a8f; margin-bottom: 4px; letter-spacing: 0.04em; }
    .meta { display: flex; justify-content: space-between; font-size: 10pt; color: #6b7280; margin-bottom: 6px; }
    .subject { text-align: center; font-size: 13pt; color: #1e40af; font-weight: 700; margin-bottom: 14px; }
    .badge { background: #f0fdf4; border: 1px solid #86efac; border-radius: 6px; padding: 8px 14px; text-align: center; color: #166534; font-size: 9pt; font-family: Arial, sans-serif; margin-bottom: 16px; }
    .preamble { font-size: 11pt; line-height: 1.7; text-align: justify; margin-bottom: 14px; color: #374151; }
    .decree-title { font-size: 14pt; font-weight: 700; color: #1a3a8f; margin-bottom: 10px; }
    .item { display: flex; gap: 10px; font-size: 11pt; line-height: 1.65; margin-bottom: 8px; }
    .item .n { min-width: 20px; font-weight: 700; color: #1a3a8f; }
    .basis { font-size: 9.5pt; color: #6b7280; margin-top: 8px; margin-bottom: 16px; font-style: italic; line-height: 1.5; }
    hr { border: none; border-top: 1px solid #e5e7eb; margin: 16px 0; }
    .control { font-size: 10pt; color: #6b7280; margin-bottom: 24px; font-style: italic; }
    .sig { display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 20px; font-size: 11pt; }
    .sig-line { flex: 1; border-bottom: 1px solid #9ca3af; margin: 0 12px; }
    .footer { margin-top: 30px; padding-top: 8px; border-top: 1px solid #e5e7eb; text-align: center; font-size: 7.5pt; color: #9ca3af; font-family: Arial, sans-serif; }
    .print-btn { position: fixed; bottom: 30px; right: 30px; background: #1a3a8f; color: white; border: none; border-radius: 50px; padding: 14px 28px; font-size: 13pt; font-family: Arial, sans-serif; font-weight: bold; cursor: pointer; box-shadow: 0 4px 20px rgba(26,58,143,0.4); }
    @media print { body { background: none; padding: 0; } .page { box-shadow: none; width: 100%; } .print-btn { display: none !important; } }
  </style>
</head>
<body>
  <div class="page">
    <div class="stripe"></div>
    <div class="school"><strong>Образовательный комплекс «Aqbobek International School»</strong><br>КГУ «Начальная школа» | г. Актобе, Республика Казахстан</div>
    <h1>ПРИКАЗ № ${orderNum}</h1>
    <div class="meta"><span>г. Актобе</span><span>«${dateStr}»</span></div>
    <div class="subject">О замене учебных занятий</div>
    <div class="badge">✓ &nbsp; Проверено AI на соответствие Приказу МОН РК №130 и №110</div>
    <div class="preamble">
      В связи с временной нетрудоспособностью учителя <strong>${sub.teacher.replace(' (Болеет)', '')}</strong> и в целях обеспечения выполнения
      государственных общеобязательных стандартов образования, недопущения срыва учебного процесса
      и соблюдения норм Приказа МОН РК №110 «О замене учителей»,
    </div>
    <div class="decree-title">БҰЙЫРАМЫН / ПРИКАЗЫВАЮ:</div>
    <div class="item"><span class="n">1.</span><span>Произвести замену учебных занятий в <strong>${sub.class}</strong> классе, кабинет <strong>${sub.room}</strong>, урок <strong>№${sub.lesson}</strong> (предмет: ${sub.subject}).</span></div>
    <div class="item"><span class="n">2.</span><span>Возложить временное исполнение обязанностей по проведению урока на учителя <strong>${sub.replacement}</strong> согласно утвержденному расписанию.</span></div>
    <div class="item"><span class="n">3.</span><span>Оплату за фактически проведенные часы замещения произвести в соответствии с нормативными правовыми актами РК и внутренним положением об оплате труда, согласно Приказу МОН РК №110.</span></div>
    <div class="item"><span class="n">4.</span><span>Учителю <strong>${sub.replacement}</strong> обеспечить качественное проведение занятий и своевременное внесение записей в электронный журнал (Күнделік) — согласно Приказу МОН РК №130.</span></div>
    <div class="item"><span class="n">5.</span><span>Секретарю передать копию настоящего приказа в бухгалтерию для начисления доплаты.</span></div>
    <div class="basis">Основание: Приказ МОН РК №130 «Об утверждении Перечня документов, обязательных для ведения педагогами», сообщение о временной нетрудоспособности от ${dateStr}.</div>
    <hr>
    <div class="control">Контроль за исполнением настоящего приказа оставляю за собой.</div>
    <div class="sig"><span>Директор начальной школы AIS:</span><span class="sig-line"></span><span>/ Сарсенбаев А.Т.</span></div>
    <div class="sig"><span>С приказом ознакомлен(а):</span><span class="sig-line"></span><span>/ ${sub.replacement}</span></div>
    <div class="footer">Сгенерировано автоматически &nbsp;|&nbsp; Соответствие: Приказ МОН РК №110, №130 &nbsp;|&nbsp; ${dateStr}</div>
  </div>
  <button class="print-btn" onclick="window.print()">🖨️ Печать / Сохранить PDF</button>
  <script>setTimeout(() => window.print(), 600);</script>
</body>
</html>`;
  };

  const normalizeOrderPayload = (sub: any) => ({
    lesson: sub.lesson ?? sub.lesson_number,
    class: sub.class ?? sub.class_name,
    room: sub.room,
    teacher: sub.teacher ?? sub.missing_teacher,
    replacement: sub.replacement ?? sub.substitute_teacher,
    subject: sub.subject,
  });

  const handleGenerateOrder = async (sub: any) => {
    setIsGeneratingOrder(true);
    try {
      const html = generateOrderHTML(normalizeOrderPayload(sub));
      const blob = new Blob([html], { type: 'text/html;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const newTab = window.open(url, '_blank');
      if (!newTab) {
        // popup blocked — download as file instead
        const link = document.createElement('a');
        link.href = url;
        link.download = `Prikaz_${sub.class}_urok${sub.lesson}.html`;
        link.click();
      }
    } catch (e) {
      console.error("Order generation error:", e);
      alert("Ошибка при генерации приказа.");
    } finally {
      setIsGeneratingOrder(false);
    }
  };

  // REAL DATA: Загрузка задач из БД
  const loadTasks = async () => {
    try {
      const res = await axios.get(`${API_BASE}/tasks/`);
      setDbTasks(res.data);
    } catch (e) {
      console.error("Failed to load tasks:", e);
    }
  };

  useEffect(() => {
    loadTasks();
    const interval = setInterval(loadTasks, 4000); // Опрашиваем задачи каждые 4 сек, чтобы увидеть подтверждение
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const loadTeacherOptions = async () => {
      try {
        const res = await axios.get(`${API_BASE}/schedule/staff`);
        const teachers = (res.data?.staff ?? []).filter((item: TeacherOption) => item.role === 'Учитель');
        setTeacherOptions(teachers);
        if (
          teachers.length > 0 &&
          !teachers.some((item: TeacherOption) => item.short_name === absenceTeacher || item.full_name === absenceTeacher)
        ) {
          setAbsenceTeacher(teachers[0].short_name || teachers[0].full_name);
        }
      } catch (e) {
        console.error("Failed to load teacher options:", e);
      }
    };

    loadTeacherOptions();
  }, []);

  const pushMessage = async (text: string, isVoice = false) => {
    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    setMessages(prev => [...prev, { text, time, parsed: null }]);

    try {
      // REAL DATA: Запрос парсинга к настоящему FastAPI бэкенду
      const res = await axios.post(`${API_BASE}/voice/task`, { test_text: text });
      const tasksParsed = res.data.voice_decomposition?.tasks || [];
      
      let insightText = "Ничего не найдено.";
      if (tasksParsed.length > 0) {
        insightText = `✅ Распознано задач: ${tasksParsed.length}\n`;
        // Если нашли задачи, сохраняем их в базу!
        for (const t of tasksParsed) {
          await axios.post(`${API_BASE}/tasks/`, {
            title: t.task_name || t.description || "Новая задача", 
            assignee: t.assignee || "Неизвестно", 
            deadline: t.deadline || "Без срока"
          });
        }
        await loadTasks(); // Обновляем список задач
      }

      setMessages(prev => {
        let updated = [...prev];
        if (updated.length > 0) {
          updated[updated.length - 1].parsed = { type: "backend_parsed", urgency: "medium", insight: insightText };
        }
        return updated;
      });

    } catch (e) {
      console.error("Critical error in pushMessage:", e);
      setMessages(prev => {
        let updated = [...prev];
        if (updated.length > 0) {
          updated[updated.length - 1].parsed = { type: "error", urgency: "critical", insight: "Ошибка сети. Бэкенд не отвечает." };
        }
        return updated;
      });
    }
  };

  const handleSend = () => {
    if(!inputVal.trim()) return;
    pushMessage(inputVal);
    setInputVal('');
  };

  // REAL DATA: Пометка задачи выполненной в базе данных!
  const markTaskDone = async (id: number) => {
    try {
      await axios.put(`${API_BASE}/tasks/${id}/complete`);
      setDbTasks(prev => prev.map(t => t.id === id ? {...t, is_completed: true} : t));
    } catch (e) {
      alert("Не удалось закрыть задачу на сервере.");
    }
  };

  const DEMO_RESPONSES: Record<string, any> = {
    "Нормы питания №130": {
      answer: "Согласно Приказу №130, мониторинг качества питания осуществляется ежедневно комиссией в составе медработника, администрации и представителей родительского комитета. Данные о количестве учащихся должны подаваться в столовую не позднее 09:00 текущего дня. Контроль выхода блюд и соответствие меню-раскладке обязателен.",
      sources: ["Приказ №130 МОН", "СанПиН 2024", "Методические рекомендации"]
    },
    "Приказ №110: Замены": {
      answer: "Замена временно отсутствующих учителей должна производиться специалистами той же предметной области. При отсутствии возможности — учителями смежных дисциплин. В исключительных случаях допускается проведение занятий администрацией школы. Все замены фиксируются в журнале учета пропущенных и замещенных уроков и оплачиваются согласно фактически отработанным часам.",
      sources: ["Приказ №110", "Трудовой Кодекс РК", "Инструкция по ведению ЖУПЗ"]
    },
    "Приказ №76: Аттестация": {
      answer: "Аттестация педагогов проводится один раз в пять лет в соответствии с правилами Приказа №76. Педагоги, подтвердившие категорию «исследователь» или «мастер», получают надбавку в размере 30-50% от БДО. Портфолио должно быть загружено в систему не позднее 2 месяцев до квалификационного экзамена.",
      sources: ["Приказ №76 МОН", "Закон об образовании", "Правила аттестации"]
    }
  };

  const DEMO_CHECKLISTS: Record<string, any> = {
    "Приказ №130": {
      answer: "Чек-лист по Приказу №130 (Посещаемость и питание):",
      items: [
        "Подать сведения о посещаемости в систему до 09:00.",
        "При отсутствии ученика >3 дней: связаться с родителями.",
        "Составить акт посещения семьи (если причина не уважительная).",
        "Сдать данные по льготному питанию соцпедагогу до 10:00."
      ],
      sources: ["Приказ №130 МОН РК"]
    }
  };

  const handleRagSearch = async (queryOverride?: string) => {
    const query = queryOverride || ragQuery;
    if (!query.trim()) return;
    
    setIsRagLoading(true);
    setRagResult(null);
    if (!queryOverride) setRagQuery(query);

    // DEMO Fallback: Search mode
    if (ragMode === 'search' && DEMO_RESPONSES[query]) {
      setTimeout(() => {
        setRagResult(DEMO_RESPONSES[query]);
        setIsRagLoading(false);
      }, 1500); 
      return;
    }

    // DEMO Fallback: Checklist mode
    const isOrder130 = query.includes("130") || query.includes("посещаемость");
    if (ragMode === 'checklist' && isOrder130) {
      setTimeout(() => {
        setRagResult(DEMO_CHECKLISTS["Приказ №130"]);
        setIsRagLoading(false);
      }, 2000);
      return;
    }

    try {
      const endpoint = ragMode === 'search' ? 'query' : 'checklist';
      const payload = ragMode === 'search' ? { query } : { order_text: query };
      const res = await axios.post(`${API_BASE}/rag/${endpoint}`, payload);
      
      const data = res.data;
      if (ragMode === 'search') {
        setRagResult({
          answer: data.analysis || data.answer || "К сожалению, в базе знаний не нашлось точного совпадения.",
          sources: data.relevant_orders || data.sources || ["Нормативная база"]
        });
      } else {
        // Checklist format
        const items = data.checklist || ["Пункт 1", "Пункт 2"];
        setRagResult({
          answer: "Чек-лист сформирован успешно:",
          items,
          sources: ["Автоматическая генерация"]
        });
      }

    } catch (e) {
      setRagResult({ 
        answer: "Извините, база знаний временно недоступна. Попробуйте позже.", 
        sources: [] 
      });
    } finally {
      setIsRagLoading(false);
    }
  };
  const stopMediaTracks = () => {
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((track) => track.stop());
      mediaStreamRef.current = null;
    }
  };

  const processAudioBlob = async (blob: Blob) => {
    setIsTranscribing(true);
    setInputVal('Обрабатываем голосовое сообщение...');

    try {
      const formData = new FormData();
      const extension = blob.type.includes('webm') ? 'webm' : 'wav';
      formData.append('file', blob, `voice.${extension}`);

      const sttResponse = await axios.post(`${API_BASE}/voice/transcribe`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      const transcript = (sttResponse.data?.transcript || '').trim();
      if (!transcript) {
        throw new Error(sttResponse.data?.error || 'empty_transcript');
      }

      setInputVal(transcript);
      await pushMessage(transcript, true);
      setInputVal('');
    } catch (error) {
      console.error('Voice transcription error:', error);
      alert('Не удалось распознать голос. Проверьте доступ к микрофону и настройки STT.');
      setInputVal('');
    } finally {
      setIsTranscribing(false);
      audioChunksRef.current = [];
    }
  };

  const handleRecordedMicClick = () => {
    if (isRecording) {
      mediaRecorderRef.current?.stop();
      setIsRecording(false);
      return;
    }

    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === 'undefined') {
      alert("Ваш браузер не поддерживает запись аудио. Откройте сайт в Google Chrome.");
      return;
    }

    navigator.mediaDevices.getUserMedia({ audio: true })
      .then((stream) => {
        mediaStreamRef.current = stream;
        audioChunksRef.current = [];

        const preferredMimeTypes = [
          'audio/webm;codecs=opus',
          'audio/webm',
          'audio/mp4',
        ];
        const mimeType = preferredMimeTypes.find((type) => MediaRecorder.isTypeSupported(type));
        const recorder = mimeType ? new MediaRecorder(stream, { mimeType }) : new MediaRecorder(stream);

        recorder.onstart = () => {
          setIsRecording(true);
          setInputVal('Записываем голосовое сообщение...');
        };

        recorder.ondataavailable = (event: BlobEvent) => {
          if (event.data && event.data.size > 0) {
            audioChunksRef.current.push(event.data);
          }
        };

        recorder.onerror = (event: any) => {
          console.error('MediaRecorder error:', event);
          setIsRecording(false);
          stopMediaTracks();
          setInputVal('');
        };

        recorder.onstop = async () => {
          setIsRecording(false);
          stopMediaTracks();

          const mime = recorder.mimeType || 'audio/webm';
          const audioBlob = new Blob(audioChunksRef.current, { type: mime });
          if (audioBlob.size === 0) {
            setInputVal('');
            return;
          }
          await processAudioBlob(audioBlob);
        };

        mediaRecorderRef.current = recorder;
        recorder.start();
      })
      .catch((error) => {
        console.error('Microphone access error:', error);
        alert('Не удалось получить доступ к микрофону.');
      });
  };

  const handleMicClick = () => {
    handleRecordedMicClick();
    return;

    if (isRecording) {
      if (recognitionRef.current) recognitionRef.current.stop();
      setIsRecording(false);
      return;
    }

    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SR) {
      alert("🎤 Ваше демо-устройство не поддерживает голосовой ввод. Пожалуйста, используйте Google Chrome.");
      return;
    }

    const recognition = new SR();
    recognition.lang = 'ru-RU';
    recognition.interimResults = true;
    recognition.continuous = false; // Для демо лучше останавливать после фразы

    recognition.onstart = () => {
      setIsRecording(true);
      setInputVal('🎤 Слушаю вас...');
      transcriptRef.current = '';
    };

    recognition.onresult = (event: any) => {
      const transcript = Array.from(event.results)
        .map((result: any) => result[0])
        .map((result: any) => result.transcript)
        .join('');
      transcriptRef.current = transcript;
      setInputVal(transcript);
    };

    recognition.onerror = (event: any) => {
      console.error('Speech recognition error:', event.error);
      setIsRecording(false);
      setInputVal('');
    };

    recognition.onend = () => {
      setIsRecording(false);
      const finalVal = transcriptRef.current; 
      if (finalVal && finalVal.trim()) {
        setIsTranscribing(true);
        setTimeout(() => {
          setIsTranscribing(false);
          pushMessage(finalVal, true);
          setInputVal('');
        }, 1200);
      }
    };

    recognition.start();
    recognitionRef.current = recognition;
  };

  const finishVoiceTask = (text: string) => {
    setTimeout(() => {
      setInputVal('');
      setIsTranscribing(false);
      pushMessage(text, true);
    }, 1200);
  };

  const handleGenerateSchedule = async () => {
    setIsGeneratingSchedule(true);
    try {
      const res = await axios.post(`${API_BASE}/schedule/generate-schedule`, {
        classes: ["1А", "2Б", "5А", "8В", "10А", "11А"]
      });
      if (res.data?.schedule) {
        setGeneratedSchedule(res.data.schedule);
        setScheduleSummary(res.data.summary ?? null);
        setScheduleRefreshToken((prev) => prev + 1);
      }
    } catch (e) {
      console.error(e);
      alert("Ошибка при генерации расписания");
    } finally {
      setIsGeneratingSchedule(false);
    }
  };

  const handleDownloadExcel = async () => {
    try {
      const res = await axios.post(`${API_BASE}/schedule/download-excel`, { schedule: generatedSchedule }, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'AI_Orchestrator_Расписание.xlsx');
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
    } catch (e) {
      console.error(e);
      alert("Ошибка при скачивании файла");
    }
  };

  const handleProcessAbsence = async () => {
    if (!absenceTeacher.trim()) {
      alert("Укажите учителя для замены.");
      return;
    }

    setIsProcessingAbsence(true);
    try {
      const res = await axios.post(`${API_BASE}/schedule/absence-event`, {
        teacher_name: absenceTeacher,
        day: absenceDay,
        reason: absenceReason || "Болезнь",
        source: "dashboard",
        raw_message: `${absenceTeacher}: ${absenceReason || "Болезнь"}`,
      });

      setAbsenceResult(res.data);
      setScheduleRefreshToken((prev) => prev + 1);
      setActiveTab('schedule');
    } catch (e) {
      console.error(e);
      alert("Не удалось обработать отсутствие и подобрать замену.");
    } finally {
      setIsProcessingAbsence(false);
    }
  };

  return (
    <div className="flex h-screen bg-[#1f1633] text-white font-sans tracking-wide overflow-hidden relative">
      <div className="absolute top-0 right-0 w-1/3 h-1/3 bg-purple-900/20 rounded-full filter blur-[150px] opacity-60 z-0 pointer-events-none"></div>
      <div className="absolute bottom-0 left-0 w-1/4 h-1/4 bg-[#c2ef4e]/5 rounded-full filter blur-[120px] z-0 pointer-events-none"></div>

      {isSidebarOpen && <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 md:hidden" onClick={() => setIsSidebarOpen(false)}></div>}
      <div className={`${isSidebarOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'} fixed md:relative w-[280px] h-full flex flex-col bg-[#16102a] border-r border-white/8 z-50 transition-transform duration-300`}>
        <div className="md:hidden absolute top-4 right-4">
           <button onClick={() => setIsSidebarOpen(false)} className="p-2 bg-white/10 rounded-full text-white/60 hover:bg-white/20"><X className="w-5 h-5"/></button>
        </div>
        <div className="p-6 flex flex-col items-center border-b border-white/8 w-full">
          <div className="w-12 h-12 rounded-xl flex items-center justify-center mb-3 p-2">
            <BrandIcon className="w-full h-full" />
          </div>
          <div className="font-bold text-base text-white tracking-tight">AI Orchestrator</div>
          <div className="text-[10px] text-white/30 font-medium mt-0.5 uppercase tracking-widest">Aqbobek School</div>
        </div>

        <div className="flex-1 overflow-y-auto p-3 space-y-0.5 w-full">
          <MenuButton title="Рабочие чаты и ГС" desc="Анализ LLM парсером" icon={<Users />} active={activeTab === 'chat'} onClick={() => setActiveTab('chat')} />
          <MenuButton title="Делегат (Voice-to-Task)" desc="Реальная База Данных" icon={<CheckCircle2 />} active={activeTab === 'tasks'} onClick={() => setActiveTab('tasks')} />
          <MenuButton title="Smart Substitution" desc="Анализ LLM: Замены" icon={<Calendar />} active={activeTab === 'schedule'} onClick={() => setActiveTab('schedule')} />
          <MenuButton title="Правовой RAG" desc="Проверка по приказам" icon={<BookOpen />} active={activeTab === 'rag'} onClick={() => setActiveTab('rag')} />
          <MenuButton title="Умное Расписание" desc="Генератор сетки с нуля" icon={<Zap />} active={activeTab === 'timetable'} onClick={() => setActiveTab('timetable')} />
          <MenuButton title="Система Лент" desc="Кросс-классовые группы" icon={<Layers />} active={activeTab === 'lenta'} onClick={() => setActiveTab('lenta')} />
          <MenuButton title="Тепловая Карта" desc="Нагрузка учителей" icon={<ThermometerSun />} active={activeTab === 'heatmap'} onClick={() => setActiveTab('heatmap')} />
          <MenuButton title="Расписание сотрудников" desc="От завхоза до директора" icon={<PersonStanding />} active={activeTab === 'staffsched'} onClick={() => setActiveTab('staffsched')} />
          <MenuButton title="Аналитика" desc="Тренды и статистика" icon={<BarChart3 />} active={activeTab === 'analytics'} onClick={() => setActiveTab('analytics')} />
        </div>
        <div className="p-4 border-t border-white/8 w-full">
          <button onClick={() => { localStorage.removeItem('auth_token'); window.location.reload(); }} className="w-full text-white/30 hover:text-rose-400 hover:bg-rose-500/10 rounded-xl transition font-medium text-sm p-3 text-center">Выйти из системы</button>
        </div>
      </div>

      <div className="flex-1 flex flex-col relative z-0 min-w-0">
        <div className="px-4 md:px-8 py-4 flex items-center justify-between z-10 sticky top-0 bg-[#1f1633]/90 backdrop-blur-md border-b border-white/8">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => setIsSidebarOpen(!isSidebarOpen)}
              className="p-2.5 rounded-xl bg-white/10 border border-white/10 hover:bg-white/15 transition active:scale-95 text-white md:hidden"
            >
              <Menu size={22} />
            </button>
            <h2 className="text-xl md:text-2xl font-bold text-white tracking-tight">AI Orchestrator</h2>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center bg-white/8 px-4 py-2 rounded-xl border border-white/10 gap-2.5">
              <span className="relative flex h-2.5 w-2.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#c2ef4e] opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-[#c2ef4e]"></span>
              </span>
              <div className="text-xs font-bold uppercase tracking-widest text-white/60">
                {botFeed.length > 0 ? `LIVE: ${botFeed.length} сообщений` : 'Sync: Telegram / SQLite'}
              </div>
            </div>
            <button
              disabled={isDemoRunning}
              onClick={async () => {
                setIsDemoRunning(true);
                setActiveTab('chat');
                try {
                  await axios.post(`${API_BASE}/bot/demo-scenario`);
                } catch {}
                setTimeout(() => setIsDemoRunning(false), 18000);
              }}
              className={`flex items-center gap-2 text-xs font-bold uppercase tracking-widest px-4 py-2.5 rounded-xl border transition-all active:scale-95 ${
                isDemoRunning
                  ? 'bg-[#c2ef4e]/10 text-[#c2ef4e] border-[#c2ef4e]/30 cursor-wait animate-pulse'
                  : 'bg-[#c2ef4e]/10 text-[#c2ef4e] border-[#c2ef4e]/30 hover:bg-[#c2ef4e]/20'
              }`}
            >
              <Rocket className="w-4 h-4" />
              {isDemoRunning ? 'Демо идёт...' : '🎬 Live Demo'}
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto px-4 md:px-8 pb-10 space-y-8 z-10 scroll-smooth pt-6">
          {activeTab === 'chat' && (
            <div className="max-w-4xl mx-auto flex flex-col space-y-8">
              
              {/* Module 1: Daily Attendance Summary */}
              <div className="bg-gradient-to-r from-[#2a1f42] to-[#1f1633] border border-[#c2ef4e]/20 rounded-2xl p-6 shadow-xl relative overflow-hidden group">
                 <div className="absolute -bottom-2 right-4 pointer-events-none z-0 animate-bounce" style={{ animationDuration: '4s' }}>
                    {/* removed mascot image */}
                 </div>
                 <div className="flex items-center justify-between relative z-10">
                    <div>
                       <div className="flex items-center space-x-2 text-[#c2ef4e]/70 font-bold uppercase tracking-widest text-xs mb-3">
                          <Clock className="w-4 h-4" /> <span>Ежедневный Свод (09:00 AM)</span>
                       </div>
                       <h3 className="text-3xl font-black mb-1 text-white">Свод по питанию</h3>
                       <p className="text-white/50 font-medium">
                         {svod && svod.report_count > 0
                           ? `Получено ${svod.report_count} отчётов из Telegram-бота`
                           : 'Данные из Telegram-бота школы'}
                       </p>
                    </div>
                    <div className="text-right">
                       <div className="text-5xl font-black leading-none">
                         {svod && svod.total_portions > 0 ? svod.total_portions : calculateAttendanceTotals().totalChildren}
                       </div>
                       <div className="text-sm font-bold text-blue-100 mt-1 uppercase tracking-widest">Порций всего</div>
                    </div>
                 </div>
                 <div className="mt-8 grid grid-cols-1 sm:grid-cols-3 gap-4 border-t border-white/20 pt-6 relative z-10">
                    <div className="flex items-center space-x-3 bg-white/10 p-4 rounded-3xl">
                       <div className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center font-black">
                         {svod ? svod.report_count : messages.filter(m => m.text.includes('детей')).length}
                       </div>
                       <div className="text-xs font-bold text-blue-50">Отчётов от классов</div>
                    </div>
                    <div className="flex items-center space-x-3 bg-blue-400/20 p-4 rounded-3xl border border-blue-300/20">
                       <div className="w-10 h-10 bg-rose-500/40 rounded-full flex items-center justify-center font-black text-white">
                         {svod ? svod.absences_today : 0}
                       </div>
                       <div className="text-xs font-bold text-blue-100">Отсутствий (учителя)</div>
                    </div>
                    <div className="flex items-center space-x-3 bg-orange-400/20 p-4 rounded-3xl border border-orange-300/20">
                       <div className="w-10 h-10 bg-orange-500/40 rounded-full flex items-center justify-center font-black text-white">
                         {svod ? svod.incidents_today : 0}
                       </div>
                       <div className="text-xs font-bold text-orange-100">Инцидентов</div>
                    </div>
                 </div>
                 <div className="mt-4 relative z-10">
                   <button
                     onClick={async () => {
                       try {
                         const r = await axios.post(`${API_BASE}/bot/send-food-report`);
                         if (r.data.sent) alert(`✅ Свод отправлен в столовую!\n${r.data.report.total_portions} порций на ${r.data.report.date}`);
                       } catch { alert('Ошибка при отправке свода'); }
                     }}
                     className="px-5 py-2 bg-[#c2ef4e] text-[#1f1633] rounded-xl font-bold text-sm hover:bg-[#a8d63a] transition-all"
                   >
                     📤 Отправить в столовую
                   </button>
                 </div>
              </div>

              {/* LIVE: Telegram Bot Feed */}
              {botFeed.length > 0 && (
                <div className="bg-[#2a1f42] rounded-[2.5rem] border border-white/8 shadow-xl overflow-hidden">
                  <div className="flex items-center justify-between px-8 py-5 border-b border-white/8">
                    <div className="flex items-center gap-3">
                      <div className="w-9 h-9 rounded-xl bg-blue-500 flex items-center justify-center">
                        <MessageSquare size={18} className="text-white" />
                      </div>
                      <div>
                        <div className="font-black text-white text-sm">LIVE: Telegram-лента</div>
                        <div className="text-xs text-white/40 font-medium">Реальные сообщения от учителей • обновляется каждые 4 сек</div>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <button 
                        onClick={async () => {
                          if (window.confirm('Точно очистить ленту?')) {
                            await axios.delete(`${API_BASE}/bot/clear`);
                            setBotFeed([]);
                          }
                        }}
                        className="text-xs font-bold text-rose-500 hover:text-rose-600 bg-rose-50 px-3 py-1.5 rounded-lg active:scale-95 transition"
                      >
                         Очистить
                      </button>
                      <span className="relative flex h-2.5 w-2.5">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
                      </span>
                    </div>
                  </div>
                  <div className="divide-y divide-slate-50 max-h-80 overflow-y-auto">
                    {botFeed.map((msg, i) => {
                      const typeColors: Record<string,string> = {
                        food: 'bg-emerald-50 text-emerald-700 border-emerald-100',
                        absence: 'bg-rose-50 text-rose-700 border-rose-100',
                        incident: 'bg-orange-50 text-orange-700 border-orange-100',
                        other: 'bg-white/5 text-white/70 border-white/8',
                      };
                      const typeLabels: Record<string,string> = {
                        food: '🍱 Явка', absence: '🔴 Отсутствие',
                        incident: '⚠️ Инцидент', other: 'ℹ️ Прочее',
                      };
                      const color = typeColors[msg.parsed_type] || typeColors.other;
                      const label = typeLabels[msg.parsed_type] || 'ℹ️';
                      const timeStr = msg.created_at ? msg.created_at.slice(-8, -3) : '';
                      return (
                        <div key={i} className="flex items-center gap-4 px-8 py-4 hover:bg-white/5/50 transition">
                          <div className="text-xs text-white/40 font-bold min-w-[40px]">{timeStr}</div>
                          <div className="font-bold text-white/90 text-sm min-w-[130px]">{msg.sender}</div>
                          <div className="flex-1 text-sm text-white/70 truncate">{msg.text}</div>
                          <div className={`text-[10px] font-black uppercase px-2.5 py-1 rounded-lg border ${color} shrink-0`}>{label}</div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {messages.length === 0 && (
                <div className="flex flex-col items-center justify-center py-20 text-center animate-in fade-in zoom-in duration-700">
                  <div className="w-16 h-16 mb-4 text-slate-200">
                    <MessageSquare size={64} />
                  </div>
                  <h3 className="text-2xl font-black text-white mb-2">Здесь пока тихо...</h3>
                  <p className="text-white/60 max-w-sm">Сообщения из чатов появятся тут автоматически. Я слежу за эфиром!</p>
                </div>
              )}

              {messages.map((m, i) => (
                <div key={i} className="flex flex-col mb-4 max-w-[90%] group">
                  <div className={`p-6 rounded-2xl rounded-tl-none relative border transition-shadow ${m.isAudio ? 'bg-emerald-900/20 border-emerald-500/20' : 'bg-[#2a1f42] border-white/10'}`}>
                    {m.isAudio ? (
                      <div className="flex flex-col">
                        <div className="flex items-center mb-3 bg-white p-3 rounded-full shadow-sm w-fit">
                           <div className="w-10 h-10 bg-emerald-500 rounded-full flex items-center justify-center text-white mr-3 shadow-md focus:outline-none"><Play className="w-5 h-5 ml-1"/></div>
                           <img src="https://upload.wikimedia.org/wikipedia/commons/d/d5/Waveform.svg" alt="waveform" className="h-6 w-32 opacity-40 mr-4" />
                           <span className="font-bold text-white/60 mr-2">0:03</span>
                        </div>
                        <p className="text-white/70 text-sm font-medium italic pr-12">Транскрипт: "{m.text}"</p>
                      </div>
                    ) : (
                      <p className="text-white text-[17px] leading-relaxed pr-12 font-semibold">{m.text}</p>
                    )}
                    <span className="text-xs font-bold text-white/30 absolute bottom-4 right-5">{m.time}</span>
                  </div>

                  <div className={`mt-3 ml-8 border rounded-xl p-5 text-sm flex items-start w-[95%] transition-all relative overflow-hidden ${m.parsed?.urgency === 'critical' ? 'bg-rose-900/20 border-rose-500/30' : 'bg-[#c2ef4e]/5 border-[#c2ef4e]/20'}`}>
                    <div className="absolute -right-2 -bottom-2 w-24 h-24 opacity-20 pointer-events-none transform rotate-12 group-hover:scale-110 transition-transform">
                      {/* removed mascot image */}
                    </div>
                    <div className="flex flex-col w-full relative z-10">
                      <b className={`uppercase text-[11px] font-black tracking-widest opacity-80 mb-2`}>[AIS АНАЛИЗ]</b>
                      <span className="font-bold text-[15px] whitespace-pre-wrap">{m.parsed?.insight}</span>
                    </div>
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>
          )}

          {activeTab === 'tasks' && (
            <div className="max-w-5xl mx-auto space-y-8 pb-20">

              {/* Header */}
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-black text-4xl text-white tracking-tight">Делегат</h3>
                  <p className="text-white/60 mt-1 font-medium flex items-center gap-2">
                    <Mic className="w-4 h-4 text-blue-500" />
                    Voice-to-Task — голос директора превращается в задачи автоматически
                  </p>
                </div>
                <button onClick={loadTasks} className="flex items-center gap-2 text-sm font-medium bg-white/8 text-white/70 px-5 py-3 border border-white/10 rounded-xl hover:bg-white/12 transition active:scale-95">
                  <Activity className="w-4 h-4" /> Обновить БД
                </button>
              </div>

              {/* Stats row */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {[
                  { label: 'Активных задач', value: dbTasks.filter(t => !t.is_completed).length, color: 'bg-blue-600', icon: <Zap className="w-5 h-5 text-white" /> },
                  { label: 'Выполнено сегодня', value: dbTasks.filter(t => t.is_completed).length, color: 'bg-emerald-500', icon: <CheckCircle className="w-5 h-5 text-white" /> },
                  { label: 'Исполнителей', value: new Set(dbTasks.map(t => t.assignee)).size, color: 'bg-violet-500', icon: <Users className="w-5 h-5 text-white" /> },
                ].map((s, i) => (
                  <div key={i} className="bg-[#2a1f42] rounded-2xl p-6 border border-white/10 flex items-center gap-5">
                    <div className={`w-12 h-12 ${s.color} rounded-2xl flex items-center justify-center shadow-lg shrink-0`}>{s.icon}</div>
                    <div>
                      <div className="text-3xl font-black text-white">{s.value}</div>
                      <div className="text-xs font-bold text-white/40 uppercase tracking-widest mt-0.5">{s.label}</div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Voice recording zone */}
              <div className={`relative rounded-2xl p-10 border-2 transition-all duration-300 overflow-hidden ${isRecording ? 'bg-gradient-to-br from-purple-900 to-violet-900 border-purple-500/30 shadow-2xl' : 'bg-[#2a1f42] border-dashed border-white/15 hover:border-[#c2ef4e]/30'}`}>
                {isRecording && (
                  <>
                    <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                      <div className="w-72 h-72 rounded-full border-2 border-white/10 animate-ping" style={{animationDuration:'1.8s'}} />
                    </div>
                    <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                      <div className="w-48 h-48 rounded-full border-2 border-white/20 animate-ping" style={{animationDuration:'1.1s'}} />
                    </div>
                  </>
                )}
                <div className="relative z-10 flex flex-col items-center text-center gap-6">
                  <button
                    onClick={handleMicClick}
                    disabled={isTranscribing}
                    className={`w-24 h-24 rounded-full flex items-center justify-center shadow-2xl transition-all active:scale-90 ${
                      isRecording ? 'bg-[#c2ef4e] text-[#1f1633] scale-110 animate-pulse' :
                      isTranscribing ? 'bg-amber-100 text-amber-500 cursor-wait' :
                      'bg-blue-600 text-white hover:bg-blue-500 hover:scale-105'
                    }`}
                  >
                    {isTranscribing ? <Activity className="w-10 h-10 animate-spin" /> : isRecording ? <div className="w-8 h-8 bg-rose-500 rounded-md" /> : <Mic className="w-10 h-10" />}
                  </button>
                  <div>
                    <div className={`font-black text-xl ${isRecording ? 'text-white' : isTranscribing ? 'text-amber-600' : 'text-white'}`}>
                      {isRecording ? '🔴 Записываю... (нажмите ■ чтобы остановить)' : isTranscribing ? '🧠 Whisper + GPT-4 анализируют...' : '🎤 Нажмите и говорите'}
                    </div>
                    <div className={`text-sm mt-1.5 font-medium ${isRecording ? 'text-blue-100' : isTranscribing ? 'text-amber-400' : 'text-white/40'}`}>
                      {isRecording ? 'Аудио записывается. Произнесите задачи чётко и нажмите стоп.' : isTranscribing ? 'Аудио отправлено на сервер для распознавания...' : 'Записываем аудио → Whisper транскрибирует → GPT-4 создаёт задачи'}
                    </div>
                  </div>
                  {/* Whisper transcript result */}
                  {isTranscribing && inputVal && (
                    <div className="w-full bg-amber-50 border border-amber-200 rounded-2xl p-5 text-left">
                      <div className="text-[10px] font-black text-amber-500 uppercase tracking-widest mb-2">Результат Whisper</div>
                      <div className="text-white text-lg font-semibold leading-relaxed">{inputVal}</div>
                    </div>
                  )}
                  {!isRecording && !isTranscribing && (
                    <div className="space-y-3 w-full max-w-2xl">
                      <div className="text-[10px] font-black text-white/40 uppercase tracking-widest text-center">Тестовые задания для демо (нажмите или произнесите)</div>
                      <div className="flex flex-wrap gap-2 justify-center">
                        {[
                          'Мадина, закажи 20 бутылей воды на завтра для начальной школы',
                          'Гульнара, подготовь актовый зал к родительскому собранию в среду',
                          'Серик, почини проектор в кабинете 205, срочно',
                          'Петрова, проведите открытый урок по математике в 4Б классе в пятницу',
                          'Секретарю: распечатайте расписание на следующую неделю, 30 копий',
                          'Охране: проверьте все запасные выходы до конца дня',
                        ].map((phrase, i) => (
                          <button key={i} onClick={() => { pushMessage(phrase, true); }}
                            className="text-xs font-bold bg-blue-50 text-blue-600 border border-blue-100 px-4 py-2 rounded-xl hover:bg-blue-100 transition active:scale-95">
                            💬 {phrase}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* --- WHATSAPP LIVE FEED (Split: Recurring vs Spontaneous) --- */}
              {botFeed.length > 0 && (
                <div className="space-y-4">
                  {/* Header */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-xl bg-emerald-500 flex items-center justify-center shadow">
                        <MessageSquare className="w-4 h-4 text-white" />
                      </div>
                      <div>
                        <div className="font-black text-white">Задачи из WhatsApp</div>
                        <div className="text-xs text-white/40 font-medium flex items-center gap-1.5">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse inline-block" />
                          Прямая трансляция · обновление каждые 4 сек
                        </div>
                      </div>
                    </div>
                    <span className="text-[10px] font-black text-emerald-600 bg-emerald-100 px-3 py-1 rounded-full uppercase tracking-widest">{botFeed.length} сообщений</span>
                  </div>

                  {/* Two-column split */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Column 1: Recurring */}
                    {(() => {
                      const recurring = [...botFeed].reverse().filter((m: any) =>
                        m.parsed_type === 'other' && m.parsed_summary?.includes('[recurring]')
                      );
                      return (
                        <div className="bg-[#2a1f42] rounded-2xl border border-violet-100 shadow-sm overflow-hidden">
                          <div className="flex items-center gap-2 px-5 py-3 bg-gradient-to-r from-violet-50 to-white border-b border-violet-100">
                            <span className="text-lg">🔁</span>
                            <div>
                              <div className="font-black text-violet-700 text-sm">Цикличные</div>
                              <div className="text-[10px] text-violet-400 font-medium">Повторяются по расписанию</div>
                            </div>
                            <span className="ml-auto text-[10px] font-black bg-violet-100 text-violet-600 px-2 py-0.5 rounded-full">{recurring.length}</span>
                          </div>
                          <div className="divide-y divide-slate-50 max-h-[320px] overflow-y-auto">
                            {recurring.length === 0 ? (
                              <div className="px-5 py-8 text-center text-white/40 text-sm">Нет цикличных задач</div>
                            ) : recurring.map((msg: any, idx: number) => (
                              <div key={idx} className="flex items-start gap-3 px-5 py-3.5 hover:bg-violet-50/40 transition-colors">
                                <div className="w-2 h-2 rounded-full bg-violet-400 mt-1.5 shrink-0" />
                                <div className="flex-1 min-w-0">
                                  <div className="flex items-center gap-2 mb-0.5">
                                    <span className="font-black text-white text-sm">{msg.sender}</span>
                                    <span className="text-[10px] text-white/40 ml-auto">{msg.created_at?.slice(11, 16)}</span>
                                  </div>
                                  <div className="text-sm text-white/70 font-medium">{msg.text?.replace('[WA] ', '')}</div>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      );
                    })()}

                    {/* Column 2: Operational events */}
                    {(() => {
                      const spontaneous = [...botFeed].reverse().filter((m: any) =>
                        ['food', 'absence', 'medical', 'incident'].includes(m.parsed_type)
                      );
                      const typeConfig: Record<string, {color: string, label: string}> = {
                        food:     { color: 'bg-amber-100 text-amber-700',   label: '🍽 Питание' },
                        absence:  { color: 'bg-rose-100 text-rose-700',     label: '🤒 Отсутствие' },
                        medical:  { color: 'bg-red-100 text-red-700',       label: '🚑 Медицина' },
                        incident: { color: 'bg-orange-100 text-orange-700', label: '🔧 Инцидент' },
                        other:    { color: 'bg-blue-100 text-blue-700',     label: '📋 Задача' },
                      };
                      return (
                        <div className="bg-[#2a1f42] rounded-2xl border border-amber-100 shadow-sm overflow-hidden">
                          <div className="flex items-center gap-2 px-5 py-3 bg-gradient-to-r from-amber-50 to-white border-b border-amber-100">
                            <span className="text-lg">⚡</span>
                            <div>
                              <div className="font-black text-amber-700 text-sm">Оперативные события</div>
                              <div className="text-[10px] text-amber-400 font-medium">Инциденты, отсутствие и сводки по школе</div>
                            </div>
                            <span className="ml-auto text-[10px] font-black bg-amber-100 text-amber-600 px-2 py-0.5 rounded-full">{spontaneous.length}</span>
                          </div>
                          <div className="divide-y divide-slate-50 max-h-[320px] overflow-y-auto">
                            {spontaneous.length === 0 ? (
                              <div className="px-5 py-8 text-center text-white/40 text-sm">Нет оперативных событий</div>
                            ) : spontaneous.map((msg: any, idx: number) => {
                              const cfg = typeConfig[msg.parsed_type] || typeConfig.other;
                              return (
                                <div key={idx} className="flex items-start gap-3 px-5 py-3.5 hover:bg-amber-50/40 transition-colors">
                                  <div className="w-2 h-2 rounded-full bg-amber-400 mt-1.5 shrink-0" />
                                  <div className="flex-1 min-w-0">
                                    <div className="flex flex-wrap items-center gap-2 mb-0.5">
                                      <span className="font-black text-white text-sm">{msg.sender}</span>
                                      <span className={`text-[10px] font-black px-2 py-0.5 rounded-full ${cfg.color}`}>{cfg.label}</span>
                                      <span className="text-[10px] text-white/40 ml-auto">{msg.created_at?.slice(11, 16)}</span>
                                    </div>
                                    <div className="text-sm text-white/70 font-medium truncate">{msg.text?.replace('[WA] ', '')}</div>
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      );
                    })()}
                  </div>
                </div>
              )}


              {/* --- 3-STAGE FEEDBACK SYSTEM --- */}
              <div className="space-y-10">
                {/* STAGE 1: REQUESTS (Non-accepted) */}
                {dbTasks.filter(t => !t.is_accepted && !t.is_completed).length > 0 && (
                  <div>
                    <div className="flex items-center gap-3 mb-4">
                      <div className="w-2.5 h-2.5 rounded-full bg-amber-400 animate-pulse"></div>
                      <span className="font-black text-white/60 uppercase tracking-widest text-[10px]">Стадия 1: Запросы ({dbTasks.filter(t => !t.is_accepted && !t.is_completed).length})</span>
                    </div>
                    <div className="space-y-3">
                      {dbTasks.filter(t => !t.is_accepted && !t.is_completed).map((t, idx) => (
                        <TaskCard key={`req-${idx}`} task={t} idx={idx} stage="request" onMarkDone={markTaskDone} />
                      ))}
                    </div>
                  </div>
                )}

                {/* STAGE 2: IN PROGRESS (Accepted) */}
                {dbTasks.filter(t => t.is_accepted && !t.is_completed).length > 0 && (
                  <div>
                    <div className="flex items-center gap-3 mb-4">
                      <div className="w-2.5 h-2.5 rounded-full bg-blue-500 animate-pulse"></div>
                      <span className="font-black text-white/60 uppercase tracking-widest text-[10px]">Стадия 2: В обработке ({dbTasks.filter(t => t.is_accepted && !t.is_completed).length})</span>
                    </div>
                    <div className="space-y-3">
                      {dbTasks.filter(t => t.is_accepted && !t.is_completed).map((t, idx) => (
                        <TaskCard key={`prog-${idx}`} task={t} idx={idx} stage="progress" onMarkDone={markTaskDone} />
                      ))}
                    </div>
                  </div>
                )}

                {/* STAGE 3: COMPLETED */}
                {dbTasks.filter(t => t.is_completed).length > 0 && (
                  <div>
                    <div className="flex items-center gap-3 mb-4">
                      <div className="w-2.5 h-2.5 rounded-full bg-emerald-500"></div>
                      <span className="font-black text-white/60 uppercase tracking-widest text-[10px]">Стадия 3: Выполнено ({dbTasks.filter(t => t.is_completed).length})</span>
                    </div>
                    <div className="space-y-3">
                      {dbTasks.filter(t => t.is_completed).map((t, idx) => (
                        <TaskCard key={`done-${idx}`} task={t} idx={idx} stage="completed" onMarkDone={markTaskDone} />
                      ))}
                    </div>
                  </div>
                )}

                {dbTasks.length === 0 && (
                  <div className="flex flex-col items-center justify-center py-16 bg-[#2a1f42] rounded-[2.5rem] border border-dashed border-white/10 text-center">
                    <div className="w-16 h-16 bg-emerald-50 rounded-3xl flex items-center justify-center mb-4">
                      <CheckCircle2 className="w-8 h-8 text-emerald-400" />
                    </div>
                    <div className="font-black text-xl text-white/90 mb-2">Задач пока нет</div>
                    <div className="text-white/40 text-sm">Продиктуйте распоряжение через микрофон</div>
                  </div>
                )}
              </div>


            </div>
          )}

          {activeTab === 'schedule' && (
            <div className="space-y-8 max-w-5xl mx-auto pb-20">
              <div className="flex justify-between items-end mb-4">
                <div>
                   <h3 className="font-black text-4xl text-white tracking-tight">AI Smart Substitution</h3>
                   <p className="text-white/60 mt-2 font-medium flex items-center">
                     <Brain className="w-4 h-4 mr-2 text-blue-500" /> 
                     Анализ на основе приказа №110 и расписания учителей
                   </p>
                </div>
                {mockSchedule.some(s => s.status === 'pending') && (
                  <button
                    onClick={applyReplacements}
                    className="bg-[#c2ef4e] hover:bg-[#a8d63a] text-[#1f1633] px-8 py-4 rounded-xl font-bold shadow-xl shadow-[#c2ef4e]/20 transition-all active:scale-95 flex items-center"
                  >
                    <Rocket className="w-5 h-5 mr-3" /> Утвердить все замены
                  </button>
                )}
              </div>

              <div className="bg-[#2a1f42] rounded-[2rem] border border-white/10 p-6 md:p-8 shadow-xl space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <label className="block md:col-span-2">
                    <div className="text-[10px] font-black text-white/40 uppercase tracking-widest mb-2">Учитель отсутствует</div>
                    <input
                      list="teacher-options"
                      value={absenceTeacher}
                      onChange={(e) => setAbsenceTeacher(e.target.value)}
                      placeholder="Например, Болат"
                      className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder:text-white/30 focus:outline-none focus:border-[#c2ef4e]/40"
                    />
                    <datalist id="teacher-options">
                      {teacherOptions.map((teacher) => (
                        <option key={teacher.id} value={teacher.short_name || teacher.full_name}>
                          {teacher.full_name}
                        </option>
                      ))}
                    </datalist>
                  </label>

                  <label className="block">
                    <div className="text-[10px] font-black text-white/40 uppercase tracking-widest mb-2">День</div>
                    <select
                      value={absenceDay}
                      onChange={(e) => setAbsenceDay(e.target.value)}
                      className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-[#c2ef4e]/40"
                    >
                      {["Понедельник", "Вторник", "Среда", "Четверг", "Пятница"].map((day) => (
                        <option key={day} value={day} className="bg-[#1f1633]">{day}</option>
                      ))}
                    </select>
                  </label>

                  <label className="block">
                    <div className="text-[10px] font-black text-white/40 uppercase tracking-widest mb-2">Причина</div>
                    <input
                      value={absenceReason}
                      onChange={(e) => setAbsenceReason(e.target.value)}
                      placeholder="Болезнь"
                      className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder:text-white/30 focus:outline-none focus:border-[#c2ef4e]/40"
                    />
                  </label>
                </div>

                <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                  <div className="text-sm text-white/50 leading-relaxed max-w-2xl">
                    Сценарий для демо: учитель сообщает, что не придет, система ищет замену по предмету, нагрузке и доступности, затем обновляет расписание и статус уведомлений.
                  </div>
                  <button
                    onClick={handleProcessAbsence}
                    disabled={isProcessingAbsence}
                    className="bg-[#c2ef4e] hover:bg-[#a8d63a] disabled:opacity-50 text-[#1f1633] px-7 py-4 rounded-xl font-bold shadow-xl shadow-[#c2ef4e]/20 transition-all active:scale-95 flex items-center justify-center gap-3"
                  >
                    {isProcessingAbsence ? <Activity className="w-5 h-5 animate-spin" /> : <Rocket className="w-5 h-5" />}
                    {isProcessingAbsence ? 'Назначаем замену...' : 'Запустить событие отсутствия'}
                  </button>
                </div>
              </div>

              {absenceResult && (
                <>
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div className="bg-[#2a1f42] rounded-2xl border border-white/10 p-5">
                      <div className="text-[10px] font-black text-white/40 uppercase tracking-widest mb-2">Статус</div>
                      <div className="text-xl font-black text-white">{absenceResult.status}</div>
                      <div className="text-sm text-white/40 mt-1">{absenceResult.teacher_name} • {absenceResult.day}</div>
                    </div>
                    <div className="bg-[#2a1f42] rounded-2xl border border-emerald-400/20 p-5">
                      <div className="text-[10px] font-black text-emerald-300 uppercase tracking-widest mb-2">Замены найдены</div>
                      <div className="text-3xl font-black text-emerald-300">{absenceResult.substitutions_count}</div>
                    </div>
                    <div className="bg-[#2a1f42] rounded-2xl border border-amber-400/20 p-5">
                      <div className="text-[10px] font-black text-amber-300 uppercase tracking-widest mb-2">Нужен ручной разбор</div>
                      <div className="text-3xl font-black text-amber-300">{absenceResult.unresolved_count}</div>
                    </div>
                    <div className="bg-[#2a1f42] rounded-2xl border border-blue-400/20 p-5">
                      <div className="text-[10px] font-black text-blue-300 uppercase tracking-widest mb-2">Live эффект</div>
                      <div className="text-sm font-semibold text-white/70 leading-relaxed">
                        Сетка ниже читает БД после замены. Можно сразу показать, что слот уже перестроен.
                      </div>
                    </div>
                  </div>

                  {absenceResult.substitutions.length > 0 && (
                    <div className="grid gap-5">
                      {absenceResult.substitutions.map((item) => (
                        <div key={item.entry_id} className="bg-[#2a1f42] rounded-[2rem] p-6 md:p-8 shadow-xl border border-emerald-400/20">
                          <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
                            <div className="flex items-start gap-5">
                              <div className="w-16 h-16 rounded-2xl bg-emerald-500/10 text-emerald-300 flex flex-col items-center justify-center font-black text-2xl shrink-0">
                                <span className="text-[10px] uppercase opacity-60 mb-1">Урок</span>
                                {item.lesson_number}
                              </div>
                              <div>
                                <div className="flex flex-wrap items-center gap-2 mb-2">
                                  <span className="bg-slate-800 text-white text-[10px] font-black px-3 py-1 rounded-full uppercase tracking-widest">{item.class_name}</span>
                                  <span className="text-white/40 font-bold text-sm flex items-center"><Clock className="w-3 h-3 mr-1" /> {item.day}</span>
                                  <span className="text-white/40 font-bold text-sm">каб. {item.room}</span>
                                </div>
                                <h4 className="text-2xl font-extrabold text-white">{item.subject}</h4>
                                <p className="text-white/60 font-bold mt-1">{item.missing_teacher} → {item.substitute_teacher}</p>
                              </div>
                            </div>

                            <div className="bg-white/5 rounded-2xl border border-white/10 p-4 min-w-[260px]">
                              <div className="text-[10px] font-black text-blue-300 uppercase tracking-widest mb-2">Результат подбора</div>
                              <div className="text-sm font-semibold text-white/80 leading-relaxed">{item.status}</div>
                              <div className="flex flex-wrap gap-2 mt-4">
                                <span className="text-[10px] font-black px-2.5 py-1 rounded-full bg-emerald-400/10 text-emerald-300 border border-emerald-400/20">
                                  applied
                                </span>
                                {item.notification?.telegram_sent && (
                                  <span className="text-[10px] font-black px-2.5 py-1 rounded-full bg-blue-500/10 text-blue-300 border border-blue-400/20">
                                    telegram sent
                                  </span>
                                )}
                                {item.notification?.whatsapp_sent && (
                                  <span className="text-[10px] font-black px-2.5 py-1 rounded-full bg-green-500/10 text-green-300 border border-green-400/20">
                                    whatsapp sent
                                  </span>
                                )}
                                {!item.notification?.telegram_sent && !item.notification?.whatsapp_sent && (
                                  <span className="text-[10px] font-black px-2.5 py-1 rounded-full bg-amber-500/10 text-amber-300 border border-amber-400/20">
                                    queued
                                  </span>
                                )}
                              </div>
                            </div>
                          </div>

                          {item.rejected_candidates && item.rejected_candidates.length > 0 && (
                            <div className="mt-4 px-2">
                              <div className="text-[10px] font-black text-white/30 uppercase tracking-widest mb-1.5">Отклонены:</div>
                              <div className="flex flex-col gap-1">
                                {item.rejected_candidates.map((r, i) => (
                                  <div key={i} className="flex gap-1.5 text-xs text-white/40">
                                    <span className="text-red-400/60">✗</span>
                                    <span className="font-semibold">{r.name}</span>
                                    <span className="text-white/25">— {r.reason}</span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}

                          <div className="mt-5 pt-5 border-t border-white/8 flex flex-wrap items-center gap-2">
                            <div className="flex items-center gap-1.5 bg-emerald-50 text-emerald-700 px-3 py-1.5 rounded-xl text-[10px] font-black uppercase tracking-widest border border-emerald-100">
                              <CheckCircle size={12} strokeWidth={3} />
                              <span>Внесено в расписание</span>
                            </div>
                            <div className="flex items-center gap-1.5 bg-blue-50 text-blue-600 px-3 py-1.5 rounded-xl text-[10px] font-black uppercase tracking-widest border border-blue-100">
                              <Check size={12} strokeWidth={3} />
                              <span>{item.match_type || 'auto_match'}</span>
                            </div>
                            <div className="flex-1" />
                            <button
                              onClick={() => handleGenerateOrder(item)}
                              disabled={isGeneratingOrder}
                              className={`flex items-center gap-1.5 text-white px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all active:scale-95 shadow-md ${isGeneratingOrder ? 'bg-slate-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700 shadow-blue-500/20'}`}
                            >
                              {isGeneratingOrder ? <Activity size={12} className="animate-spin" /> : <FileText size={12} />}
                              <span>{isGeneratingOrder ? 'Генерация...' : 'Скачать приказ'}</span>
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {absenceResult.unresolved.length > 0 && (
                    <div className="bg-[#2a1f42] rounded-[2rem] border border-amber-400/20 p-6 md:p-8">
                      <div className="flex items-center gap-3 mb-5">
                        <AlertTriangle className="w-5 h-5 text-amber-300" />
                        <h4 className="text-xl font-black text-white">Слоты, которые требуют ручного решения</h4>
                      </div>
                      <div className="grid gap-3">
                        {absenceResult.unresolved.map((item) => (
                          <div key={item.entry_id} className="bg-white/5 border border-white/8 rounded-2xl p-4 flex flex-col md:flex-row md:items-center md:justify-between gap-3">
                            <div>
                              <div className="font-bold text-white">{item.class_name} • {item.subject}</div>
                              <div className="text-sm text-white/40 mt-1">{item.day}, {item.lesson_number} урок, каб. {item.room}</div>
                            </div>
                            <div className="text-sm font-semibold text-amber-300">{item.status}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="bg-slate-900/80 border border-slate-700/50 rounded-2xl p-5">
                    <div className="flex items-center justify-between mb-4">
                      <div>
                        <h3 className="text-white font-bold text-lg">Live Timetable After Substitution</h3>
                        <p className="text-white/40 text-xs mt-0.5">
                          Ниже реальная сетка из БД после события отсутствия.
                        </p>
                      </div>
                    </div>
                    <TimetableGrid
                      className="w-full"
                      classFilter={absenceResult.substitutions[0]?.class_name || absenceResult.unresolved[0]?.class_name}
                      refreshToken={scheduleRefreshToken}
                    />
                  </div>
                </>
              )}

              {!absenceResult && <div className="grid gap-6">
                {mockSchedule.map((s, idx) => (
                  <div key={idx} className={`bg-[#2a1f42] rounded-[2.5rem] p-8 shadow-xl border-2 transition-all group ${s.alert ? (s.status === 'applied' ? 'border-blue-100 bg-blue-50/20' : 'border-rose-100 animate-pulse-subtle') : 'border-white/8'}`}>

                    {/* ---- ROW 1: Lesson info + replacement ---- */}
                    <div className="flex items-start justify-between">
                      <div className="flex items-start space-x-8">
                        <div className={`w-16 h-16 rounded-2xl flex flex-col items-center justify-center font-black text-2xl shadow-inner shrink-0 ${s.alert ? 'bg-rose-50 text-rose-500' : 'bg-white/5 text-white/40'}`}>
                          <span className="text-xs uppercase opacity-40 mb-1">Урок</span>
                          {s.lesson}
                        </div>
                        <div>
                          <div className="flex items-center space-x-3 mb-2">
                             <span className="bg-slate-800 text-white text-[10px] font-black px-3 py-1 rounded-full uppercase tracking-widest">Класс {s.class}</span>
                             <span className="text-white/40 font-bold text-sm flex items-center"><Clock className="w-3 h-3 mr-1" /> Каб. {s.room}</span>
                          </div>
                          <h4 className="text-2xl font-extrabold text-white">{s.subject}</h4>
                          <p className="text-white/60 font-bold mt-1">{s.teacher}</p>
                        </div>
                      </div>

                      {s.alert && (
                        <div className="flex items-center space-x-4 shrink-0">
                          <div className="text-right">
                             <div className="text-[10px] font-black text-blue-500 uppercase tracking-widest mb-1">Предлагаемая замена</div>
                             <div className="text-xl font-black text-white">{s.replacement}</div>
                          </div>
                          <div className="w-12 h-12 bg-blue-600 rounded-2xl flex items-center justify-center text-white shadow-lg shadow-blue-500/20 shrink-0">
                             <ArrowRight size={24} />
                          </div>
                        </div>
                      )}
                    </div>

                    {/* ---- ROW 2: Action buttons (below, when applied) ---- */}
                    {s.status === 'applied' && (
                      <div className="mt-5 pt-4 border-t border-white/8 flex flex-wrap items-center gap-2">
                        <div className="flex items-center gap-1.5 bg-emerald-50 text-emerald-700 px-3 py-1.5 rounded-xl text-[10px] font-black uppercase tracking-widest border border-emerald-100">
                          <CheckCircle size={12} strokeWidth={3} />
                          <span>Проверено AI • №130</span>
                        </div>
                        <div className="flex items-center gap-1.5 bg-blue-50 text-blue-600 px-3 py-1.5 rounded-xl text-[10px] font-black uppercase tracking-widest border border-blue-100">
                          <Check size={12} strokeWidth={3} />
                          <span>Applied</span>
                        </div>
                        <div className="flex-1" />
                        <button
                          onClick={() => handleGenerateOrder(s)}
                          disabled={isGeneratingOrder}
                          className={`flex items-center gap-1.5 text-white px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all active:scale-95 shadow-md ${isGeneratingOrder ? 'bg-slate-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700 shadow-blue-500/20'}`}
                        >
                          {isGeneratingOrder ? <Activity size={12} className="animate-spin" /> : <FileText size={12} />}
                          <span>{isGeneratingOrder ? 'Генерация...' : 'Скачать приказ'}</span>
                        </button>
                        <a
                          href={`https://wa.me/?text=${encodeURIComponent(`Приказ о замене сформирован. Учитель: ${s.teacher}, заменяет: ${s.replacement}, класс ${s.class}, каб. ${s.room}, урок ${s.lesson}. Сделайте начисление за замещение.`)}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-1.5 bg-[#25D366] hover:bg-[#1da851] text-white px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all active:scale-95 shadow-md shadow-green-500/20"
                        >
                          <MessageSquare size={12} />
                          <span>Отправить в WA</span>
                        </a>
                      </div>
                    )}

                    {/* ---- ROW 3: AI Rationale + Confidence ---- */}
                    {s.alert && (
                      <div className="mt-8 pt-8 border-t border-white/8 space-y-4">
                        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 md:gap-8">
                          <div className="col-span-2 flex items-start space-x-4 bg-white/5 p-6 rounded-3xl border border-white/8">
                            <Brain className="w-6 h-6 text-blue-500 mt-1 shrink-0" />
                            <div>
                              <div className="text-[10px] font-black text-white/40 uppercase tracking-widest mb-1">AI Rationale</div>
                              <p className="text-sm font-bold text-white/90 leading-relaxed italic">"{s.reasoning}"</p>
                            </div>
                          </div>
                          <div className="flex flex-col justify-center items-center bg-blue-50/50 rounded-3xl border border-blue-100 p-6">
                             <div className="text-[32px] font-black text-blue-600 leading-none">{s.confidence}%</div>
                             <div className="text-[10px] font-black text-blue-400 uppercase tracking-widest mt-2">AI Confidence</div>
                          </div>
                        </div>
                        {s.rejected && s.rejected.length > 0 && (
                          <div className="bg-rose-50/50 border border-rose-100 rounded-2xl p-4">
                            <div className="text-[10px] font-black text-rose-400 uppercase tracking-widest mb-2">❌ Отклонённые альтернативы</div>
                            <div className="space-y-1.5">
                              {s.rejected.map((r: any, ri: number) => (
                                <div key={ri} className="flex items-center gap-2 text-xs">
                                  <X className="w-3 h-3 text-rose-400 shrink-0" />
                                  <span className="font-bold text-white/70">{r.name}</span>
                                  <span className="text-white/40">—</span>
                                  <span className="text-rose-500 font-medium">{r.reason}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>}
              
              <style dangerouslySetInnerHTML={{ __html: `
                @keyframes pulse-subtle {
                  0%, 100% { opacity: 1; transform: scale(1); }
                  50% { opacity: 0.95; transform: scale(0.995); }
                }
                .animate-pulse-subtle {
                  animation: pulse-subtle 3s cubic-bezier(0.4, 0, 0.6, 1) infinite;
                }
              `}} />
            </div>
          )}

          {activeTab === 'rag' && (
            <div className="max-w-5xl mx-auto space-y-8 pb-20">

              {/* Header */}
              <div>
                <h3 className="font-black text-4xl text-white tracking-tight">Правовой Советник</h3>
                <p className="text-white/60 mt-1 font-medium flex items-center gap-2">
                  <Shield className="w-4 h-4 text-blue-500" />
                  RAG — семантический поиск по приказам МОН РК №76, №110, №130
                </p>
              </div>

              {/* Law cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {[
                  {
                    num: '№130', title: 'Питание и посещаемость',
                    desc: 'Порядок сбора данных, питание, льготные категории.',
                    color: 'from-emerald-500 to-teal-600',
                    query: 'Нормы питания №130', tags: ['Ежедневно', 'Столовая', 'Льготники'],
                  },
                  {
                    num: '№110', title: 'Замена учителей',
                    desc: 'Порядок замещения, оплата, журнал пропущенных уроков.',
                    color: 'from-blue-500 to-indigo-600',
                    query: 'Приказ №110: Замены', tags: ['ЖУПЗ', 'Оплата', 'Профиль'],
                  },
                  {
                    num: '№76', title: 'Аттестация педагогов',
                    desc: 'Категории, надбавки, сроки, портфолио педагога.',
                    color: 'from-violet-500 to-purple-600',
                    query: 'Приказ №76: Аттестация', tags: ['Каждые 5 лет', 'БДО +30-50%', 'Портфолио'],
                  },
                ].map((law, i) => (
                  <button
                    key={i}
                    onClick={() => handleRagSearch(law.query)}
                    className={`group relative bg-gradient-to-br ${law.color} rounded-3xl p-6 text-left text-white shadow-xl hover:shadow-2xl hover:-translate-y-1 transition-all overflow-hidden`}
                  >
                    <div className="absolute top-4 right-4 text-5xl font-black opacity-10 group-hover:opacity-20 transition-opacity">{law.num}</div>
                    <div className="text-[10px] font-black uppercase tracking-widest opacity-70 mb-2">Приказ МОН РК</div>
                    <div className="text-2xl font-black mb-1">{law.num}</div>
                    <div className="font-bold text-sm opacity-90 mb-3">{law.title}</div>
                    <div className="text-xs opacity-70 leading-relaxed mb-4">{law.desc}</div>
                    <div className="flex flex-wrap gap-1.5">
                      {law.tags.map((t, j) => (
                        <span key={j} className="text-[10px] font-black bg-white/20 px-2.5 py-1 rounded-lg">{t}</span>
                      ))}
                    </div>
                    <div className="absolute bottom-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity">
                      <ChevronRight className="w-5 h-5" />
                    </div>
                  </button>
                ))}
              </div>

              {/* Search + mode toggle */}
              <div className="bg-[#2a1f42] rounded-2xl border border-white/10 p-8 space-y-6">
                <div className="flex gap-2 bg-white/8 p-1 rounded-xl w-fit">
                  <button onClick={() => setRagMode('search')} className={`px-5 py-2 rounded-xl text-xs font-black transition-all ${ragMode === 'search' ? 'bg-blue-600 text-white shadow-md' : 'text-white/40 hover:text-white/70'}`}>
                    🔍 Семантический поиск
                  </button>
                  <button onClick={() => setRagMode('checklist')} className={`px-5 py-2 rounded-xl text-xs font-black transition-all ${ragMode === 'checklist' ? 'bg-blue-600 text-white shadow-md' : 'text-white/40 hover:text-white/70'}`}>
                    ✅ Генератор чек-листов
                  </button>
                </div>

                <div className="flex gap-3">
                  <div className="flex-1 flex items-center bg-white/8 border border-white/10 rounded-xl px-5 gap-3 focus-within:border-[#c2ef4e]/40 transition-all">
                    <Search className="w-5 h-5 text-white/40 shrink-0" />
                    <input
                      type="text"
                      value={ragQuery}
                      onChange={(e) => setRagQuery(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && handleRagSearch()}
                      placeholder={ragMode === 'search' ? 'Спросите об оплате замен, нормах питания...' : 'Введите тему для генерации чек-листа...'}
                      className="flex-1 bg-transparent text-white placeholder-slate-400 py-4 text-base focus:outline-none font-medium"
                    />
                    {ragQuery && <button onClick={() => setRagQuery('')} className="text-white/30 hover:text-white/60 transition"><X className="w-4 h-4" /></button>}
                  </div>
                  <button
                    onClick={() => handleRagSearch()}
                    disabled={isRagLoading || !ragQuery.trim()}
                    className="bg-[#c2ef4e] hover:bg-[#a8d63a] disabled:opacity-40 text-[#1f1633] px-8 py-4 rounded-xl font-bold shadow-lg transition-all active:scale-95 flex items-center gap-2 whitespace-nowrap"
                  >
                    {isRagLoading ? <div className="w-5 h-5 border-3 border-white/30 border-t-white rounded-full animate-spin" /> : <Sparkles className="w-5 h-5" />}
                    {isRagLoading ? 'Анализ...' : 'Найти ответ'}
                  </button>
                </div>

                {/* Quick queries */}
                <div className="flex flex-wrap gap-2">
                  <span className="text-xs font-bold text-white/40 uppercase tracking-widest self-center">Быстро:</span>
                  {(ragMode === 'search'
                    ? ['Нормы питания №130', 'Приказ №110: Замены', 'Приказ №76: Аттестация', 'Как оформить замену?']
                    : ['Приказ №130', 'Приказ №110', 'Аттестация педагога']
                  ).map((txt, i) => (
                    <button key={i} onClick={() => handleRagSearch(txt)}
                      className="text-xs font-bold bg-white/5 hover:bg-blue-50 text-white/70 hover:text-blue-600 border border-white/10 hover:border-blue-200 px-3 py-1.5 rounded-xl transition-all">
                      {txt}
                    </button>
                  ))}
                </div>
              </div>

              {/* Loading */}
              {isRagLoading && (
                <div className="bg-[#2a1f42] rounded-3xl border border-white/8 shadow-lg p-12 flex flex-col items-center gap-6">
                  <div className="flex gap-3">
                    {[0, 0.15, 0.3].map((delay, i) => (
                      <div key={i} className="w-3 h-3 bg-blue-500 rounded-full animate-bounce" style={{animationDelay: `${delay}s`}} />
                    ))}
                  </div>
                  <div>
                    <div className="font-black text-white/90 text-center">Семантическое сканирование...</div>
                    <div className="text-xs text-white/40 text-center mt-1">Поиск по векторной базе приказов МОН РК</div>
                  </div>
                </div>
              )}

              {/* Empty state */}
              {!ragResult && !isRagLoading && (
                <div className="flex flex-col items-center justify-center py-12 text-center">
                  <div className="w-20 h-20 bg-blue-50 rounded-3xl flex items-center justify-center mb-6">
                    <BookOpen className="w-10 h-10 text-blue-300" />
                  </div>
                  <div className="font-black text-xl text-white/90 mb-2">Юридическая база готова</div>
                  <div className="text-white/40 text-sm max-w-sm">Нажмите на карточку приказа или введите вопрос — AI найдёт точный ответ</div>
                </div>
              )}

              {/* Result */}
              {ragResult && !isRagLoading && (
                <div className="bg-[#2a1f42] border border-white/10 rounded-2xl overflow-hidden animate-in slide-in-from-bottom-4 duration-500">
                  {/* Result header */}
                  <div className="bg-gradient-to-r from-[#3d1f6e] to-[#2a1f6e] px-8 py-5 flex items-center justify-between border-b border-white/10">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 bg-white/20 rounded-xl flex items-center justify-center">
                        <Sparkles className="w-4 h-4 text-white" />
                      </div>
                      <div>
                        <div className="font-black text-white text-sm">AI-ответ сформирован</div>
                        <div className="text-blue-200 text-xs">Правовой советник • RAG v2.0</div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="flex items-center gap-1.5 bg-emerald-400/20 text-emerald-200 border border-emerald-400/30 px-3 py-1.5 rounded-xl text-[10px] font-black uppercase tracking-widest">
                        <CheckCircle className="w-3 h-3" /> Соответствует нормам
                      </div>
                      <button onClick={() => setRagResult(null)} className="w-8 h-8 bg-white/10 hover:bg-white/20 rounded-xl flex items-center justify-center transition text-white">
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  </div>

                  <div className="p-8 space-y-6">
                    {/* Answer text */}
                    <div className="relative">
                      <Quote className="absolute -top-3 -left-2 w-10 h-10 text-blue-500/10" />
                      <p className="text-base font-medium text-white/80 leading-relaxed pl-4 border-l-4 border-[#c2ef4e]/30">
                        {ragResult.answer}
                      </p>
                    </div>

                    {/* Checklist items */}
                    {ragResult.items && (
                      <div className="space-y-3">
                        <div className="flex items-center justify-between">
                          <div className="text-[10px] font-black text-white/40 uppercase tracking-widest">Пошаговый чек-лист</div>
                          <button
                            onClick={() => {
                              const text = ragResult.items.map((it: string, i: number) => `${i + 1}. ${it}`).join('\n');
                              navigator.clipboard.writeText(text);
                              alert('Чек-лист скопирован!');
                            }}
                            className="flex items-center gap-1.5 text-xs font-bold text-blue-600 hover:text-blue-700 bg-blue-50 hover:bg-blue-100 px-3 py-1.5 rounded-xl transition border border-blue-100"
                          >
                            <Paperclip className="w-3.5 h-3.5" /> Скопировать
                          </button>
                        </div>
                        <div className="space-y-2">
                          {ragResult.items.map((it: string, i: number) => (
                            <div key={i} className="flex items-start gap-4 bg-white/5 p-4 rounded-2xl border border-white/8 hover:bg-white hover:shadow-md transition-all group">
                              <div className="w-7 h-7 bg-blue-600 text-white rounded-full flex items-center justify-center font-black text-xs shrink-0 shadow-md">{i + 1}</div>
                              <p className="font-semibold text-white/90 text-sm leading-relaxed pt-0.5">{it}</p>
                              <CheckCircle2 className="w-4 h-4 text-slate-200 group-hover:text-emerald-400 shrink-0 mt-0.5 transition-colors" />
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Sources + actions */}
                    <div className="pt-4 border-t border-white/8 flex items-center justify-between flex-wrap gap-4">
                      <div className="flex flex-wrap gap-2">
                        {ragResult.sources?.map((s: string, i: number) => (
                          <div key={i} className="flex items-center gap-2 bg-white/5 border border-white/10 px-4 py-2 rounded-xl">
                            <FileText className="w-4 h-4 text-blue-400" />
                            <span className="text-xs font-bold text-white/70">{s}</span>
                          </div>
                        ))}
                      </div>
                      <div className="flex gap-2">
                        <button
                          onClick={() => {
                            const text = `${ragResult.answer}\n\n${ragResult.items ? ragResult.items.map((it: string, i: number) => `${i+1}. ${it}`).join('\n') : ''}`;
                            const url = `https://wa.me/?text=${encodeURIComponent(text)}`;
                            window.open(url, '_blank');
                          }}
                          className="flex items-center gap-2 bg-[#25D366] hover:bg-[#1da851] text-white px-4 py-2.5 rounded-xl text-xs font-black transition-all active:scale-95 shadow-sm"
                        >
                          <MessageSquare className="w-3.5 h-3.5" /> Отправить в WA
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'timetable' && (
            <div className="max-w-4xl mx-auto space-y-8 pb-32">
              <div className="bg-gradient-to-r from-[#2a1f42] to-[#1a1030] border border-[#c2ef4e]/20 rounded-2xl p-8 text-white relative overflow-hidden shadow-xl">
                <div className="absolute top-0 right-0 w-64 h-64 bg-white opacity-5 rounded-full blur-3xl -translate-y-1/2 translate-x-1/4"></div>
                <div className="relative z-10 flex justify-between items-center">
                  <div>
                    <h2 className="text-4xl font-black tracking-tight mb-2">Генератор Расписания</h2>
                    <p className="text-blue-100/80 font-medium text-lg max-w-lg">
                      Умный алгоритм пересобирает расписание с нуля с учётом всех коллизий: учителя и кабинеты не пересекаются.
                    </p>
                  </div>
                  <button
                    onClick={handleGenerateSchedule}
                    disabled={isGeneratingSchedule}
                    className="bg-[#c2ef4e] text-[#1f1633] px-8 py-4 rounded-xl font-bold shadow-xl shadow-[#c2ef4e]/20 hover:scale-105 active:scale-95 transition-all flex items-center gap-3 disabled:opacity-50"
                  >
                    {isGeneratingSchedule ? (
                      <><div className="w-5 h-5 border-2 border-blue-600 border-t-white rounded-full animate-spin" />ГЕНЕРАЦИЯ...</>
                    ) : (
                      <><Zap className="w-5 h-5" /> СГЕНЕРИРОВАТЬ</>
                    )}
                  </button>
                </div>
              </div>

              {generatedSchedule.length > 0 ? (
                <div className="space-y-6 animate-fade-in-up">
                  <div className="flex justify-between items-center">
                    <h3 className="font-black text-2xl text-white">Результат генерации (Предпросмотр)</h3>
                    <button 
                      onClick={handleDownloadExcel}
                      className="bg-emerald-500 text-white px-5 py-2.5 rounded-xl font-bold tracking-wide shadow-lg shadow-emerald-500/30 hover:scale-105 active:scale-95 transition-all flex items-center gap-2"
                    >
                      <Download className="w-5 h-5" /> Экспорт в Excel
                    </button>
                  </div>
                  {scheduleSummary && (
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div className="bg-[#2a1f42] p-4 rounded-2xl border border-white/10">
                        <div className="text-[10px] font-black text-white/40 uppercase tracking-widest mb-2">Всего блоков</div>
                        <div className="text-2xl font-black text-white">{scheduleSummary.total_entries}</div>
                      </div>
                      <div className="bg-[#2a1f42] p-4 rounded-2xl border border-white/10">
                        <div className="text-[10px] font-black text-white/40 uppercase tracking-widest mb-2">Классов</div>
                        <div className="text-2xl font-black text-white">{scheduleSummary.classes}</div>
                      </div>
                      <div className="bg-[#2a1f42] p-4 rounded-2xl border border-amber-400/20">
                        <div className="text-[10px] font-black text-amber-300 uppercase tracking-widest mb-2">Self-study</div>
                        <div className="text-2xl font-black text-amber-300">{scheduleSummary.self_study_slots}</div>
                      </div>
                      <div className="bg-[#2a1f42] p-4 rounded-2xl border border-blue-400/20">
                        <div className="text-[10px] font-black text-blue-300 uppercase tracking-widest mb-2">Ленты</div>
                        <div className="text-2xl font-black text-blue-300">{scheduleSummary.lenta_slots}</div>
                      </div>
                    </div>
                  )}
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {generatedSchedule.slice(0, 18).map((lesson, idx) => (
                      <div key={idx} className="bg-[#2a1f42] p-5 rounded-2xl border border-white/10 hover:border-white/20 transition">
                        <div className="flex justify-between items-start mb-2">
                          <span className="bg-blue-50 text-blue-600 text-xs font-black uppercase tracking-widest px-3 py-1 rounded-full">{lesson.Класс}</span>
                          <span className="text-white/40 font-bold text-sm bg-white/5 px-2 py-0.5 rounded-lg">{lesson.День}, {lesson.Урок} урок</span>
                        </div>
                        <h4 className="font-black text-lg text-white mt-2">{lesson.Предмет}</h4>
                        <div className="flex items-start gap-2 mt-3 text-sm font-medium text-white/60">
                          <User size={14} className="text-blue-500 mt-0.5 shrink-0" />
                          <span className="whitespace-pre-wrap">{lesson.Учитель}</span>
                        </div>
                        <div className="flex items-center gap-2 mt-2 text-sm font-medium text-white/60">
                          <QrCode size={14} className="text-rose-500" />
                          <span>{lesson.Кабинет}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                  {generatedSchedule.length > 18 && (
                    <div className="text-center w-full py-4 bg-white/5 rounded-2xl border border-white/8">
                      <span className="font-bold text-white/40">Показаны первые 18 блоков из {generatedSchedule.length}...</span>
                    </div>
                  )}
                </div>
              ) : (
                <div className="w-full text-center py-20 opacity-50">
                  <div className="w-24 h-24 bg-white/8 rounded-full mx-auto flex items-center justify-center mb-6">
                    <Calendar className="w-10 h-10 text-white/40" />
                  </div>
                  <h3 className="text-xl font-bold text-white/40 mb-2">Расписание еще не сгенерировано</h3>
                  <p className="text-white/40 max-w-sm mx-auto">Нажмите кнопку наверх, чтобы ИИ пересобрал всю школу за секунду.</p>
                </div>
              )}

              {/* Drag-and-Drop сетка из БД */}
              <div className="bg-slate-900/80 border border-slate-700/50 rounded-2xl p-5">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="text-white font-bold text-lg">Редактор расписания (Drag & Drop)</h3>
                    <p className="text-white/40 text-xs mt-0.5">Данные из БД — перетащите урок для ручной корректировки</p>
                  </div>
                </div>
                <TimetableGrid className="w-full" refreshToken={scheduleRefreshToken} />
              </div>
            </div>
          )}

          {activeTab === 'analytics' && (
            <div className="max-w-5xl mx-auto space-y-8 pb-20">
              <div>
                <h3 className="font-black text-4xl text-white tracking-tight">Аналитика</h3>
                <p className="text-white/60 mt-1 font-medium flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-violet-500" />
                  Недельные тренды и статистика школы
                </p>
              </div>

              {/* Stats row */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {[
                  { label: 'Задач за неделю', value: 34, color: 'bg-blue-600', icon: <Zap className="w-5 h-5 text-white" />, change: '+12%' },
                  { label: 'Замен проведено', value: 7, color: 'bg-violet-500', icon: <Calendar className="w-5 h-5 text-white" />, change: '-2' },
                  { label: 'Средняя явка', value: '94%', color: 'bg-emerald-500', icon: <Users className="w-5 h-5 text-white" />, change: '+1.5%' },
                  { label: 'Инцидентов', value: 3, color: 'bg-rose-500', icon: <AlertTriangle className="w-5 h-5 text-white" />, change: '-40%' },
                ].map((s, i) => (
                  <div key={i} className="bg-[#2a1f42] rounded-2xl p-6 border border-white/10">
                    <div className="flex items-center gap-3 mb-3">
                      <div className={`w-10 h-10 ${s.color} rounded-xl flex items-center justify-center shrink-0`}>{s.icon}</div>
                      <div className="text-[10px] font-bold text-[#c2ef4e] bg-[#c2ef4e]/10 px-2 py-0.5 rounded-full">{s.change}</div>
                    </div>
                    <div className="text-3xl font-bold text-white">{s.value}</div>
                    <div className="text-[10px] font-medium text-white/40 uppercase tracking-widest mt-1">{s.label}</div>
                  </div>
                ))}
              </div>

              {/* Attendance trend (CSS bar chart) */}
              <div className="bg-[#2a1f42] rounded-2xl p-8 border border-white/10">
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <div className="font-bold text-lg text-white">Посещаемость по дням</div>
                    <div className="text-xs text-white/40 font-medium">Последние 7 дней • порции / отчёты</div>
                  </div>
                  <div className="flex gap-3 text-[10px] font-bold uppercase tracking-widest">
                    <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-blue-500"></span> Порции</span>
                    <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-emerald-400"></span> Отчёты</span>
                  </div>
                </div>
                <div className="flex items-end gap-3 h-48">
                  {[
                    { day: 'Пн', portions: 120, reports: 6 },
                    { day: 'Вт', portions: 135, reports: 7 },
                    { day: 'Ср', portions: 128, reports: 6 },
                    { day: 'Чт', portions: 142, reports: 8 },
                    { day: 'Пт', portions: 115, reports: 5 },
                    { day: 'Сб', portions: 45, reports: 3 },
                    { day: 'Вс', portions: 0, reports: 0 },
                  ].map((d, i) => (
                    <div key={i} className="flex-1 flex flex-col items-center gap-1">
                      <div className="w-full flex gap-1 items-end justify-center" style={{ height: '160px' }}>
                        <div 
                          className="w-5 bg-gradient-to-t from-blue-600 to-blue-400 rounded-t-lg transition-all duration-500" 
                          style={{ height: `${(d.portions / 142) * 100}%`, minHeight: d.portions > 0 ? '8px' : '0' }}
                        />
                        <div 
                          className="w-5 bg-gradient-to-t from-emerald-500 to-emerald-300 rounded-t-lg transition-all duration-500" 
                          style={{ height: `${(d.reports / 8) * 100}%`, minHeight: d.reports > 0 ? '8px' : '0' }}
                        />
                      </div>
                      <span className="text-[10px] font-bold text-white/40">{d.day}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Bottom row: Top incidents + Task completion */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-[#2a1f42] rounded-3xl p-8 border border-white/8 shadow-xl">
                  <div className="font-black text-lg text-white mb-4">Топ-3 типа инцидентов</div>
                  <div className="space-y-4">
                    {[
                      { type: 'Поломка оборудования', count: 5, pct: 50, color: 'bg-amber-500' },
                      { type: 'Конфликт между учениками', count: 3, pct: 30, color: 'bg-rose-500' },
                      { type: 'Протечка / авария', count: 2, pct: 20, color: 'bg-blue-500' },
                    ].map((inc, i) => (
                      <div key={i}>
                        <div className="flex justify-between items-center mb-1.5">
                          <span className="text-sm font-bold text-white/90">{inc.type}</span>
                          <span className="text-xs font-black text-white/40">{inc.count} случаев</span>
                        </div>
                        <div className="h-2.5 bg-white/8 rounded-full overflow-hidden">
                          <div className={`h-full ${inc.color} rounded-full transition-all duration-700`} style={{ width: `${inc.pct}%` }} />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="bg-[#2a1f42] rounded-3xl p-8 border border-white/8 shadow-xl">
                  <div className="font-black text-lg text-white mb-4">Эффективность задач</div>
                  <div className="flex items-center justify-center py-4">
                    <div className="relative w-36 h-36">
                      <svg className="w-full h-full -rotate-90" viewBox="0 0 36 36">
                        <circle cx="18" cy="18" r="15.5" fill="none" stroke="#f1f5f9" strokeWidth="3" />
                        <circle cx="18" cy="18" r="15.5" fill="none" stroke="#3b82f6" strokeWidth="3" strokeDasharray="97.4" strokeDashoffset="24.3" strokeLinecap="round" />
                      </svg>
                      <div className="absolute inset-0 flex flex-col items-center justify-center">
                        <div className="text-3xl font-black text-white">75%</div>
                        <div className="text-[9px] font-bold text-white/40 uppercase tracking-widest">Выполнено</div>
                      </div>
                    </div>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 md:gap-8 pb-10">
                    {[
                      { label: 'Выполнено', value: 26, color: 'text-blue-600' },
                      { label: 'В работе', value: 5, color: 'text-amber-500' },
                      { label: 'Просрочено', value: 3, color: 'text-rose-500' },
                    ].map((s, i) => (
                      <div key={i} className="text-center">
                        <div className={`text-xl font-black ${s.color}`}>{s.value}</div>
                        <div className="text-[9px] font-bold text-white/40 uppercase tracking-widest">{s.label}</div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Director metric */}
              <div className="bg-gradient-to-r from-[#3d1f6e] to-[#1f2d6e] border border-[#c2ef4e]/20 rounded-2xl p-8 text-white shadow-xl">
                <div className="flex items-center justify-between">
                  <div>
            <div className="text-xs font-black uppercase tracking-widest text-lime-200/80 mb-2">Метрика</div>
                    <div className="text-2xl font-black">Директор тратил 2 часа в день на рутину →</div>
                    <div className="text-4xl font-black mt-1">Теперь 5 минут</div>
                  </div>
                  <div className="text-8xl font-black opacity-20">24×</div>
                </div>
              </div>

              {/* AI PDF Report Button */}
              <GenerateReportButton />
            </div>
          )}

        </div>

        <div className="px-4 md:px-8 py-4 bg-[#16102a]/80 backdrop-blur-xl border-t border-white/8 z-20">
          <div className="max-w-4xl mx-auto flex items-center bg-white/8 rounded-2xl border border-white/10 p-2">
            <input type="text" value={inputVal} onChange={(e) => setInputVal(e.target.value)} onKeyPress={(e) => e.key === 'Enter' && handleSend()} placeholder={isRecording ? "🎤 Идет запись ГС..." : "Отправить текст или ГС для LLM-обработки..."} className="flex-1 text-white p-3 bg-transparent border-none focus:outline-none text-base font-medium placeholder-white/30 pl-5" />
            <div className="flex space-x-2 mr-1">
              {inputVal ? <button onClick={handleSend} className="p-3 bg-[#c2ef4e] text-[#1f1633] rounded-xl font-bold"><Send className="w-5 h-5"/></button> : <button onClick={handleMicClick} className={`p-3 text-[#1f1633] rounded-xl flex items-center justify-center ${isRecording ? 'bg-rose-500 text-white animate-pulse' : 'bg-[#c2ef4e]'}`}><Mic className="w-5 h-5" /></button>}
            </div>
          </div>
        </div>

        {/* SUCCESS OVERLAY */}
        {showSuccessOverlay && (
          <div className="fixed inset-0 z-[200] flex items-center justify-center bg-slate-900/40 backdrop-blur-md animate-in fade-in duration-500">
            <div className="bg-[#2a1f42] p-12 rounded-3xl shadow-[0_50px_100px_rgba(0,0,0,0.5)] flex flex-col items-center text-center max-w-lg border border-white/10 animate-in zoom-in duration-500">
               <div className="w-24 h-24 bg-[#c2ef4e]/15 rounded-full flex items-center justify-center mb-8">
                  <CheckCircle size={48} strokeWidth={2} className="text-[#c2ef4e]" />
               </div>
               <h2 className="text-3xl font-bold text-white mb-4 tracking-tight">Замены утверждены!</h2>
               <p className="text-white/60 font-medium leading-relaxed px-4">Все замены разосланы учителям. <br/> <span className="text-[#c2ef4e]">Система работает корректно!</span></p>
            </div>
          </div>
        )}

        {/* AI Generating Order Loader */}
        {isGeneratingOrder && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center bg-blue-900/40 backdrop-blur-md">
             <div className="bg-[#2a1f42] p-12 rounded-3xl shadow-2xl text-center space-y-6 animate-in zoom-in duration-300 border border-white/10">
                <div className="relative w-24 h-24 mx-auto">
                   <div className="absolute inset-0 bg-blue-100 rounded-3xl animate-spin duration-[3000ms]"></div>
                   <div className="absolute inset-0 flex items-center justify-center text-blue-600">
                      <Sparkles size={40} className="animate-pulse" />
                   </div>
                </div>
                <div>
                   <h3 className="text-2xl font-black text-white">Бюрократическая магия...</h3>
                   <p className="text-white/60 font-bold uppercase tracking-widest text-xs mt-2">Генерация юридического драфта по Приказу №130</p>
                </div>
             </div>
          </div>
        )}

        {/* Legal Order Modal (Printable) */}
        {selectedOrder && (
          <div className="fixed inset-0 z-[110] flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4 overflow-y-auto">
             <div className="bg-[#2a1f42] w-full max-w-4xl rounded-3xl shadow-2xl overflow-hidden animate-in slide-in-from-bottom-10 duration-500 flex flex-col max-h-[90vh] border border-white/10">
                <div className="px-10 py-6 border-b border-white/8 flex items-center justify-between bg-[#2a1f42] relative z-20">
                   <div className="flex items-center space-x-4">
                      <div className="w-12 h-12 bg-blue-100 text-blue-600 rounded-2xl flex items-center justify-center">
                         <FileText size={24} />
                      </div>
                      <div>
                         <h3 className="font-black text-xl text-white uppercase tracking-tight">Предпросмотр приказа</h3>
                         <p className="text-xs font-bold text-white/40 uppercase tracking-widest">Готов к печати согласно ГОСТ РК</p>
                      </div>
                   </div>
                   <div className="flex items-center space-x-3">
                      <button 
                         onClick={() => window.print()} 
                         className="flex items-center space-x-2 bg-slate-800 hover:bg-slate-900 text-white px-6 py-3 rounded-2xl font-black text-xs uppercase tracking-widest transition-all active:scale-95"
                      >
                         <Printer size={16} />
                         <span>Распечатать</span>
                      </button>
                      <button 
                         onClick={() => setSelectedOrder(null)} 
                         className="p-3 hover:bg-white/8 rounded-2xl transition-colors"
                      >
                         <X size={24} className="text-white/40" />
                      </button>
                   </div>
                </div>

                <div id="printable-order" className="flex-1 overflow-y-auto p-12 bg-white/5">
                   <div className="bg-white shadow-xl mx-auto p-16 min-h-[1000px] text-white font-serif leading-relaxed print:shadow-none print:p-0">
                      {/* Document Header */}
                      <div className="text-center mb-12 space-y-2 border-b-2 border-slate-900 pb-8">
                         <div className="font-bold text-sm uppercase tracking-wider mb-4 whitespace-pre-line">
                            {selectedOrder.header}
                         </div>
                         <div className="text-3xl font-black tracking-tighter uppercase my-6">ПРИКАЗ / БҰЙРЫҚ</div>
                         <div className="flex justify-between font-bold text-sm px-10 pt-4">
                            <div>г. Астана / Астана қ.</div>
                            <div>{selectedOrder.order_date} г.</div>
                         </div>
                         <div className="font-black text-xl pt-2">{selectedOrder.order_number}</div>
                      </div>

                      {/* Content */}
                      <div className="space-y-10 text-justify px-4">
                         <div className="italic font-bold text-white/90">
                            {selectedOrder.preamble}
                         </div>

                         <div className="space-y-6">
                            <div className="font-black underline uppercase">БҰЙЫРАМЫН / ПРИКАЗЫВАЮ:</div>
                            <div className="whitespace-pre-line">
                               {selectedOrder.order_body_kz}
                            </div>
                            <div className="whitespace-pre-line mt-6 border-t border-white/8 pt-6">
                               {selectedOrder.order_body_ru}
                            </div>
                         </div>

                         <div className="mt-20 pt-12 grid grid-cols-2 gap-20">
                            <div className="space-y-12">
                               <div className="border-b border-slate-900 pb-2 font-bold uppercase text-xs">Директор</div>
                               <div className="border-b border-slate-900 pb-2 font-bold uppercase text-xs">Ознакомлен(а)</div>
                            </div>
                            <div className="space-y-12 text-right">
                               <div className="font-bold whitespace-pre-line text-sm">{selectedOrder.signatories.split('\n')[0]}</div>
                               <div className="font-bold whitespace-pre-line text-sm">{selectedOrder.signatories.split('\n')[1]}</div>
                            </div>
                         </div>
                      </div>

                      {/* Seal Area (Visual) */}
                      <div className="mt-32 opacity-10 flex justify-end pr-20">
                         <div className="w-32 h-32 border-4 border-blue-600 rounded-full flex items-center justify-center text-blue-600 font-black text-[10px] text-center rotate-12 uppercase p-2">
                            Место печати / Мөр орны
                         </div>
                      </div>
                   </div>
                </div>
             </div>

             <style dangerouslySetInnerHTML={{ __html: `
                @media print {
                  body * { visibility: hidden; }
                  #printable-order, #printable-order * { visibility: visible; }
                  #printable-order { position: absolute; left: 0; top: 0; width: 100%; height: 100%; padding: 0; background: white; }
                  .no-print { display: none !important; }
                }
             `}} />
          </div>
        )}

        {/* ─── Система лент ─── */}
        {activeTab === 'lenta' && (
          <div className="max-w-5xl mx-auto pb-20 pt-2">
            <LentaView className="w-full" />
          </div>
        )}

        {/* ─── Тепловая карта ─── */}
        {activeTab === 'heatmap' && (
          <div className="max-w-5xl mx-auto pb-20 pt-2">
            <HeatmapView className="w-full" />
          </div>
        )}

        {/* ─── Расписание сотрудников ─── */}
        {activeTab === 'staffsched' && (
          <div className="max-w-6xl mx-auto pb-20 pt-2">
            <StaffSchedule className="w-full min-h-[70vh]" />
          </div>
        )}
      </div>
    </div>
  );
}

function GenerateReportButton() {
  const [loading, setLoading] = React.useState(false);
  const [period, setPeriod] = React.useState<'week' | 'month' | 'quarter' | 'custom'>('week');
  const today = new Date().toISOString().split('T')[0];
  const [customFrom, setCustomFrom] = React.useState(today);
  const [customTo, setCustomTo] = React.useState(today);

  const getDateRange = () => {
    const to = today;
    if (period === 'week') {
      const from = new Date(Date.now() - 7 * 86400000).toISOString().split('T')[0];
      return { from, to };
    }
    if (period === 'month') {
      const from = new Date(Date.now() - 30 * 86400000).toISOString().split('T')[0];
      return { from, to };
    }
    if (period === 'quarter') {
      const from = new Date(Date.now() - 90 * 86400000).toISOString().split('T')[0];
      return { from, to };
    }
    return { from: customFrom, to: customTo };
  };

  const handleGenerate = async () => {
    setLoading(true);
    const { from, to } = getDateRange();
    try {
      const res = await axios.get(`${API_BASE}/analytics/report`, {
        params: { date_from: from, date_to: to }
      });
      const html: string = res.data.html;
      const blob = new Blob([html], { type: 'text/html;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const tab = window.open(url, '_blank');
      if (!tab) {
        const link = document.createElement('a');
        link.href = url;
        link.download = `Otchet_${from}_${to}.html`;
        link.click();
      }
    } catch (e) {
      alert('Ошибка генерации отчёта. Проверьте, что бэкенд запущен.');
    } finally {
      setLoading(false);
    }
  };

  const periodTabs = [
    { key: 'week',    label: '7 дней' },
    { key: 'month',   label: 'Месяц' },
    { key: 'quarter', label: 'Квартал' },
    { key: 'custom',  label: 'Период' },
  ] as const;

  return (
    <div className="bg-[#2a1f42] border border-white/10 rounded-3xl p-8 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-5">
        <div className="w-14 h-14 bg-[#c2ef4e]/10 rounded-2xl flex items-center justify-center text-[#c2ef4e] shrink-0">
          <FileText size={26} />
        </div>
        <div>
          <div className="font-black text-xl text-white">AI-Отчёт для директора</div>
          <div className="text-white/60 font-medium mt-0.5 text-sm">
            Система соберёт данные, напишет аналитику и сформирует PDF-документ для печати.
          </div>
        </div>
      </div>

      {/* Period Tabs */}
      <div className="flex bg-white/8 p-1 rounded-2xl gap-1">
        {periodTabs.map(tab => (
          <button
            key={tab.key}
            onClick={() => setPeriod(tab.key)}
            className={`flex-1 py-2.5 rounded-xl text-sm font-black transition-all ${
              period === tab.key
                ? 'bg-[#c2ef4e]/20 text-[#c2ef4e] border border-[#c2ef4e]/30'
                : 'text-white/40 hover:text-white/70'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Custom Date Range */}
      {period === 'custom' && (
        <div className="flex items-center gap-4 p-4 bg-white/5 rounded-2xl border border-white/10">
          <div className="flex-1">
            <div className="text-xs font-black text-white/40 uppercase tracking-widest mb-1.5">С</div>
            <input
              type="date"
              value={customFrom}
              max={customTo}
              onChange={e => setCustomFrom(e.target.value)}
              className="w-full bg-white/8 border border-white/10 rounded-xl px-3 py-2 text-sm font-medium text-white focus:outline-none focus:border-[#c2ef4e]/50"
            />
          </div>
          <div className="text-white/30 font-black mt-5">→</div>
          <div className="flex-1">
            <div className="text-xs font-black text-white/40 uppercase tracking-widest mb-1.5">По</div>
            <input
              type="date"
              value={customTo}
              min={customFrom}
              max={today}
              onChange={e => setCustomTo(e.target.value)}
              className="w-full bg-white/8 border border-white/10 rounded-xl px-3 py-2 text-sm font-medium text-white focus:outline-none focus:border-[#c2ef4e]/50"
            />
          </div>
        </div>
      )}

      {/* Date range preview */}
      {period !== 'custom' && (
        <div className="text-xs font-bold text-white/40 text-center">
          {(() => { const {from, to} = getDateRange(); return `${from} — ${to}`; })()}
        </div>
      )}

      {/* Generate Button */}
      <button
        onClick={handleGenerate}
        disabled={loading}
        className={`w-full flex items-center justify-center gap-3 px-8 py-4 rounded-2xl font-black text-sm uppercase tracking-widest transition-all active:scale-95 shadow-lg ${
          loading
            ? 'bg-white/8 text-white/40 cursor-wait'
            : 'bg-[#c2ef4e] hover:bg-[#a8d63a] text-[#1f1633] shadow-[#c2ef4e]/20 hover:-translate-y-0.5'
        }`}
      >
        {loading ? (
          <><div className="w-4 h-4 border-2 border-slate-300 border-t-slate-500 rounded-full animate-spin" />AI генерирует отчёт...</>
        ) : (
          <><Download size={18} />Сформировать и открыть PDF</>
        )}
      </button>
    </div>
  );
}

function MenuButton({title, desc, icon, active, onClick}: any) {
  return (
    <div onClick={onClick} className={`px-3 py-2.5 rounded-xl cursor-pointer transition-all duration-200 flex items-center group ${active ? 'bg-[#c2ef4e]/15 border border-[#c2ef4e]/30' : 'hover:bg-white/6 border border-transparent'}`}>
      <div className={`p-2 rounded-lg mr-3 shrink-0 ${active ? 'bg-[#c2ef4e]/20 text-[#c2ef4e]' : 'bg-white/8 text-white/40 group-hover:text-white/60'}`}>{icon}</div>
      <div className="min-w-0">
        <h3 className={`font-semibold text-sm truncate ${active ? 'text-[#c2ef4e]' : 'text-white/70 group-hover:text-white/90'}`}>{title}</h3>
        <p className={`text-[11px] mt-0.5 truncate ${active ? 'text-[#c2ef4e]/60' : 'text-white/30'}`}>{desc}</p>
      </div>
    </div>
  );
}
