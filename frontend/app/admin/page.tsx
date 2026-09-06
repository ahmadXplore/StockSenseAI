"use client";

import { useEffect, useState, useRef } from "react";
import Link from "next/link";
import {
  Shield, Users, Database, Activity, UserPlus, UserX,
  UserCheck, Trash2, Edit3, Upload, RefreshCw, Search,
  AlertTriangle, CheckCircle2, XCircle, FileText, Download,
  Layers, Lock, Unlock, Server, HardDrive, Terminal, Loader2,
  Check, ArrowRight
} from "lucide-react";
import { api, AdminUser, AdminStats, AdminAuditLog } from "@/lib/api";
import { BackButton } from "@/components/BackButton";

export default function AdminDashboardPage() {
  // Security & Authentication State
  const [isAdminAuthenticated, setIsAdminAuthenticated] = useState<boolean | null>(null);
  const [isConsoleUnlocked, setIsConsoleUnlocked] = useState<boolean>(false);
  const [adminPasscode, setAdminPasscode] = useState("");
  const [passcodeError, setPasscodeError] = useState("");
  const [verifyingPasscode, setVerifyingPasscode] = useState(false);

  // State
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [auditLogs, setAuditLogs] = useState<AdminAuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"users" | "data" | "audit">("users");

  // Filter & Search
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<"all" | "active" | "blocked">("all");

  // Modals
  const [showAddUserModal, setShowAddUserModal] = useState(false);
  const [showEditUserModal, setShowEditUserModal] = useState<AdminUser | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<AdminUser | null>(null);

  // Form states (Add User)
  const [newUserName, setNewUserName] = useState("");
  const [newUserEmail, setNewUserEmail] = useState("");
  const [newUserRole, setNewUserRole] = useState("user");
  const [newUserActive, setNewUserActive] = useState(true);
  const [creatingUser, setCreatingUser] = useState(false);

  // Upload states
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [datasetType, setDatasetType] = useState("historical_prices");
  const [targetMarket, setTargetMarket] = useState("PK");
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<string | null>(null);

  // Purge states
  const [purgeTarget, setPurgeTarget] = useState("");
  const [purging, setPurging] = useState(false);
  const [actionNotice, setActionNotice] = useState<{ type: "ok" | "err"; message: string } | null>(null);

  const fileInputRef = useRef<HTMLInputElement | null>(null);

  // Check Admin Authorization & Session Lock on mount
  useEffect(() => {
    if (typeof window !== "undefined") {
      const userStr = sessionStorage.getItem("stocksense_user") || localStorage.getItem("stocksense_user");
      let isUserAdmin = false;
      if (userStr) {
        try {
          const u = JSON.parse(userStr);
          isUserAdmin = Boolean(u.is_admin || u.role === "admin");
        } catch {}
      }
      setIsAdminAuthenticated(isUserAdmin);

      const unlocked = sessionStorage.getItem("stocksense_admin_unlocked") === "true";
      setIsConsoleUnlocked(unlocked);
    }
  }, []);

  const handleUnlockConsole = (e: React.FormEvent) => {
    e.preventDefault();
    setVerifyingPasscode(true);
    setPasscodeError("");

    // Accept master security passcodes
    const validPasscodes = ["admin2026", "9928", "stocksense_admin", "admin"];
    if (validPasscodes.includes(adminPasscode.trim().toLowerCase())) {
      setIsConsoleUnlocked(true);
      if (typeof window !== "undefined") {
        sessionStorage.setItem("stocksense_admin_unlocked", "true");
      }
      setPasscodeError("");
      loadData();
    } else {
      setPasscodeError("Invalid Administrator Master Passcode. Access denied.");
    }
    setVerifyingPasscode(false);
  };

  const handleLockConsole = () => {
    setIsConsoleUnlocked(false);
    if (typeof window !== "undefined") {
      sessionStorage.removeItem("stocksense_admin_unlocked");
    }
    setAdminPasscode("");
  };

  const loadData = async () => {
    setLoading(true);
    try {
      const [s, u, a] = await Promise.allSettled([
        api.admin.stats(),
        api.admin.users(searchQuery, statusFilter !== "all" ? statusFilter : undefined),
        api.admin.auditLogs(30),
      ]);

      if (s.status === "fulfilled") setStats(s.value);
      if (u.status === "fulfilled") setUsers(u.value);
      if (a.status === "fulfilled") setAuditLogs(a.value);
    } catch (e: any) {
      console.error("Admin load error:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isConsoleUnlocked) {
      loadData();
    }
  }, [searchQuery, statusFilter, isConsoleUnlocked]);

  const handleToggleBlock = async (user: AdminUser) => {
    try {
      const res = await api.admin.toggleBlockUser(user.id);
      setActionNotice({
        type: "ok",
        message: res.message || `User status updated.`,
      });
      await loadData();
    } catch (err: any) {
      setActionNotice({ type: "err", message: err.message || "Failed to update user status." });
    }
  };

  const handleDeleteUser = async (user: AdminUser) => {
    try {
      await api.admin.deleteUser(user.id);
      setActionNotice({
        type: "ok",
        message: `User '${user.name}' permanently deleted from database.`,
      });
      setShowDeleteConfirm(null);
      await loadData();
    } catch (err: any) {
      setActionNotice({ type: "err", message: err.message || "Failed to delete user." });
    }
  };

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreatingUser(true);
    try {
      await api.admin.createUser({
        name: newUserName.trim(),
        email: newUserEmail.trim(),
        role: newUserRole,
        is_active: newUserActive,
        is_admin: newUserRole === "admin",
      });
      setShowAddUserModal(false);
      setNewUserName("");
      setNewUserEmail("");
      setActionNotice({ type: "ok", message: `New user '${newUserName}' created in database.` });
      await loadData();
    } catch (err: any) {
      setActionNotice({ type: "err", message: err.message || "Could not create user." });
    } finally {
      setCreatingUser(false);
    }
  };

  const handleUpdateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!showEditUserModal) return;
    try {
      await api.admin.updateUser(showEditUserModal.id, {
        name: showEditUserModal.name,
        email: showEditUserModal.email,
        role: showEditUserModal.role,
        is_active: showEditUserModal.is_active,
        is_admin: showEditUserModal.role === "admin" || showEditUserModal.is_admin,
      });
      setShowEditUserModal(null);
      setActionNotice({ type: "ok", message: `User profile updated.` });
      await loadData();
    } catch (err: any) {
      setActionNotice({ type: "err", message: err.message || "Could not update user." });
    }
  };

  const handleFileUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile) return;

    setUploading(true);
    setUploadResult(null);

    const formData = new FormData();
    formData.append("file", uploadFile);
    formData.append("dataset_type", datasetType);
    formData.append("market_code", targetMarket);

    try {
      const res = await api.admin.uploadData(formData);
      setUploadResult(`✅ Ingested ${res.records_accepted} records from '${res.filename}' into database.`);
      setUploadFile(null);
      if (fileInputRef.current) fileInputRef.current.value = "";
      await loadData();
    } catch (err: any) {
      setUploadResult(`❌ Upload error: ${err.message}`);
    } finally {
      setUploading(false);
    }
  };

  const handlePurge = async (target: string) => {
    if (!confirm(`Are you sure you want to purge data for '${target}'? This cannot be undone.`)) return;
    setPurging(true);
    try {
      const res = await api.admin.purgeData(target);
      setActionNotice({ type: "ok", message: res.message });
      setPurgeTarget("");
      await loadData();
    } catch (err: any) {
      setActionNotice({ type: "err", message: err.message || "Purge failed." });
    } finally {
      setPurging(false);
    }
  };

  // ─────────────────────────────────────────────────────────
  // Screen 1: Access Denied if user is not an admin
  // ─────────────────────────────────────────────────────────
  if (isAdminAuthenticated === false) {
    return (
      <div className="min-h-[70vh] flex flex-col items-center justify-center p-6 text-center space-y-5">
        <div className="h-16 w-16 rounded-2xl bg-red-500/10 border border-red-500/30 flex items-center justify-center text-red-400 shadow-2xl">
          <Lock className="h-8 w-8" />
        </div>
        <div className="space-y-2 max-w-md">
          <h2 className="text-xl font-bold text-white tracking-tight">Access Restricted</h2>
          <p className="text-xs text-gray-400 leading-relaxed">
            The Institutional Administration Console and Database Operations Hub are restricted strictly to verified system administrators. Direct URL access without administrative privileges is blocked.
          </p>
        </div>
        <div className="flex gap-3">
          <Link
            href="/dashboard"
            className="px-4 py-2.5 rounded-xl bg-background-elevated hover:bg-white/5 border border-border text-white text-xs font-semibold transition-all flex items-center gap-1.5"
          >
            <BackButton fallbackHref="/dashboard" label="Return to Dashboard" />
          </Link>
          <Link
            href="/auth"
            className="px-4 py-2.5 rounded-xl bg-brand hover:bg-brand-hover text-white text-xs font-bold transition-all shadow-md shadow-blue-500/20 flex items-center gap-1.5"
          >
            <Shield className="h-3.5 w-3.5" />
            <span>Biometric Admin Login</span>
          </Link>
        </div>
      </div>
    );
  }

  // ─────────────────────────────────────────────────────────
  // Screen 2: Passcode Verification Screen
  // ─────────────────────────────────────────────────────────
  if (!isConsoleUnlocked) {
    return (
      <div className="min-h-[70vh] flex flex-col items-center justify-center p-6">
        <form
          onSubmit={handleUnlockConsole}
          className="bg-[#0B0F19] border border-border rounded-2xl p-6 sm:p-8 max-w-md w-full shadow-2xl space-y-5 text-center"
        >
          <div className="h-14 w-14 rounded-2xl bg-brand/15 border border-brand/30 flex items-center justify-center text-brand mx-auto shadow-lg">
            <Shield className="h-7 w-7" />
          </div>

          <div className="space-y-1">
            <h2 className="text-lg font-bold text-white tracking-tight">Admin Security Verification</h2>
            <p className="text-xs text-gray-400 leading-relaxed">
              Enter your Administrator Security Passcode or Master Key to unlock database management tools and user controls.
            </p>
          </div>

          {passcodeError && (
            <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-xs font-mono text-left flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 shrink-0 text-red-400" />
              <span>{passcodeError}</span>
            </div>
          )}

          <div className="space-y-2 text-left">
            <label className="text-[11px] font-semibold text-gray-300">Security Passcode / Master PIN</label>
            <div className="relative">
              <input
                type="password"
                value={adminPasscode}
                onChange={(e) => setAdminPasscode(e.target.value)}
                placeholder="Enter admin passcode (e.g. admin2026)"
                className="w-full bg-[#12192C] border border-border rounded-xl px-4 py-2.5 text-sm text-white font-mono placeholder-gray-500 focus:border-brand focus:outline-none"
                autoFocus
                required
              />
            </div>
            <p className="text-[10px] text-gray-500">
              Default system master passcode: <span className="font-mono text-gray-400 font-semibold">admin2026</span> or <span className="font-mono text-gray-400 font-semibold">9928</span>
            </p>
          </div>

          <div className="pt-2 flex gap-3">
            <Link
              href="/dashboard"
              className="w-1/2 py-2.5 rounded-xl bg-background-elevated hover:bg-white/5 border border-border text-gray-300 hover:text-white text-xs font-semibold transition-all text-center flex items-center justify-center"
            >
              Cancel
            </Link>
            <button
              type="submit"
              disabled={verifyingPasscode || !adminPasscode.trim()}
              className="w-1/2 py-2.5 rounded-xl bg-brand hover:bg-brand-hover text-white text-xs font-bold transition-all shadow-md shadow-blue-500/20 flex items-center justify-center gap-1.5"
            >
              {verifyingPasscode ? <Loader2 className="h-4 w-4 animate-spin" /> : <Unlock className="h-4 w-4" />}
              <span>Unlock Hub</span>
            </button>
          </div>
        </form>
      </div>
    );
  }

  // ─────────────────────────────────────────────────────────
  // Screen 3: Unlocked Institutional Admin Dashboard
  // ─────────────────────────────────────────────────────────
  return (
    <div className="space-y-8 py-4">
      {/* Back Button & Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-border/60 pb-4">
        <div className="space-y-1.5">
          <div className="flex items-center gap-2">
            <BackButton fallbackHref="/dashboard" label="Back to Dashboard" />
            <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[11px] font-semibold uppercase tracking-wider">
              <Shield className="h-3 w-3" />
              <span>Admin Console: Unlocked</span>
            </div>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            Institutional Administration &amp; Data Hub
          </h1>
          <p className="text-xs sm:text-sm text-gray-400 max-w-2xl leading-relaxed">
            Manage registered users, access permissions, multi-market datasets, database records, and system telemetry with live PostgreSQL persistence.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleLockConsole}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-red-500/10 hover:bg-red-500/20 border border-red-500/30 text-red-300 text-xs font-semibold transition-all"
            title="Lock Admin Console"
          >
            <Lock className="h-3.5 w-3.5" />
            <span>Lock Console</span>
          </button>
          <button
            onClick={loadData}
            disabled={loading}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-background-elevated border border-border text-gray-300 hover:text-white text-xs font-semibold transition-all"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin text-brand" : ""}`} />
            <span>Refresh</span>
          </button>
          <button
            onClick={() => setShowAddUserModal(true)}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-brand hover:bg-brand-hover text-white text-xs font-bold transition-all shadow-md shadow-blue-500/20"
          >
            <UserPlus className="h-4 w-4" />
            <span>Add User</span>
          </button>
        </div>
      </div>

      {/* Action Notification Banner */}
      {actionNotice && (
        <div
          className={`flex items-center justify-between p-3.5 rounded-xl border text-xs font-mono animate-fadeIn ${
            actionNotice.type === "ok"
              ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-300"
              : "bg-red-500/10 border-red-500/30 text-red-300"
          }`}
        >
          <div className="flex items-center gap-2">
            {actionNotice.type === "ok" ? <CheckCircle2 className="h-4 w-4" /> : <AlertTriangle className="h-4 w-4" />}
            <span>{actionNotice.message}</span>
          </div>
          <button onClick={() => setActionNotice(null)} className="text-gray-400 hover:text-white">✕</button>
        </div>
      )}

      {/* KPI Stats Ribbon */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 font-mono text-xs">
        <div className="bg-[#0B0F19] border border-border rounded-2xl p-4 shadow-xl space-y-1">
          <div className="text-gray-400 flex items-center justify-between">
            <span>Total Enrolled Users</span>
            <Users className="h-4 w-4 text-brand" />
          </div>
          <div className="text-2xl font-extrabold text-white">
            {stats?.total_users ?? users.length}
          </div>
          <div className="text-[10px] text-emerald-400 font-sans">
            {stats?.active_users ?? users.filter(u => u.is_active).length} Active · {stats?.blocked_users ?? users.filter(u => !u.is_active).length} Blocked
          </div>
        </div>

        <div className="bg-[#0B0F19] border border-border rounded-2xl p-4 shadow-xl space-y-1">
          <div className="text-gray-400 flex items-center justify-between">
            <span>Admin Privileges</span>
            <Shield className="h-4 w-4 text-amber-400" />
          </div>
          <div className="text-2xl font-extrabold text-amber-400">
            {stats?.admin_users ?? users.filter(u => u.is_admin || u.role === "admin").length} Admins
          </div>
          <div className="text-[10px] text-gray-500 font-sans">Role-Based Access Control</div>
        </div>

        <div className="bg-[#0B0F19] border border-border rounded-2xl p-4 shadow-xl space-y-1">
          <div className="text-gray-400 flex items-center justify-between">
            <span>Master Securities</span>
            <Database className="h-4 w-4 text-brand" />
          </div>
          <div className="text-2xl font-extrabold text-white">
            {stats?.total_securities ?? 150}
          </div>
          <div className="text-[10px] text-gray-500 font-sans">Multi-Market Canonical Master</div>
        </div>

        <div className="bg-[#0B0F19] border border-border rounded-2xl p-4 shadow-xl space-y-1">
          <div className="text-gray-400 flex items-center justify-between">
            <span>Database Status</span>
            <Server className="h-4 w-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-extrabold text-emerald-400 flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-emerald-400 animate-pulse" />
            <span className="capitalize">{stats?.database_status ?? "Healthy"}</span>
          </div>
          <div className="text-[10px] text-gray-500 font-sans">PostgreSQL / TimescaleDB</div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex items-center gap-2 border-b border-border/80">
        <button
          onClick={() => setActiveTab("users")}
          className={`flex items-center gap-2 px-4 py-2.5 border-b-2 text-xs font-semibold transition-colors ${
            activeTab === "users"
              ? "border-brand text-brand bg-brand/5"
              : "border-transparent text-gray-400 hover:text-white"
          }`}
        >
          <Users className="h-4 w-4" />
          <span>User Management</span>
          <span className="px-1.5 py-0.2 rounded-full bg-background-elevated border border-border text-[10px] text-gray-300">
            {users.length}
          </span>
        </button>

        <button
          onClick={() => setActiveTab("data")}
          className={`flex items-center gap-2 px-4 py-2.5 border-b-2 text-xs font-semibold transition-colors ${
            activeTab === "data"
              ? "border-brand text-brand bg-brand/5"
              : "border-transparent text-gray-400 hover:text-white"
          }`}
        >
          <Database className="h-4 w-4" />
          <span>Dataset &amp; File Ingestion</span>
        </button>

        <button
          onClick={() => setActiveTab("audit")}
          className={`flex items-center gap-2 px-4 py-2.5 border-b-2 text-xs font-semibold transition-colors ${
            activeTab === "audit"
              ? "border-brand text-brand bg-brand/5"
              : "border-transparent text-gray-400 hover:text-white"
          }`}
        >
          <Terminal className="h-4 w-4" />
          <span>Audit Logs &amp; Activity</span>
        </button>
      </div>

      {/* TAB 1: USER MANAGEMENT */}
      {activeTab === "users" && (
        <div className="bg-[#0B0F19] border border-border rounded-2xl p-6 shadow-xl space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border/50 pb-4">
            <div>
              <h2 className="text-base font-bold text-white">Database User Accounts</h2>
              <p className="text-xs text-gray-400">
                Manage user privileges, biometric registrations, and instant block / unblock access restrictions.
              </p>
            </div>

            <div className="flex items-center gap-3">
              {/* Search */}
              <div className="relative">
                <Search className="absolute left-3 top-2.5 h-3.5 w-3.5 text-gray-500" />
                <input
                  type="text"
                  placeholder="Search user name or email..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="bg-[#12192C] border border-border rounded-xl pl-8 pr-3 py-1.5 text-xs text-white placeholder-gray-500 w-48 sm:w-60 focus:border-brand"
                />
              </div>

              {/* Status Filter */}
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value as any)}
                className="bg-[#12192C] border border-border rounded-xl px-3 py-1.5 text-xs text-white focus:border-brand"
              >
                <option value="all">All Statuses</option>
                <option value="active">Active Only</option>
                <option value="blocked">Blocked Only</option>
              </select>
            </div>
          </div>

          {/* User Table */}
          <div className="overflow-x-auto border border-border/60 rounded-xl">
            <table className="w-full text-xs font-mono text-left border-collapse">
              <thead>
                <tr className="bg-background-elevated border-b border-border/60 text-gray-400 text-[10px] uppercase">
                  <th className="py-3 px-4">User Details</th>
                  <th className="py-3 px-3">Role</th>
                  <th className="py-3 px-3">Biometrics</th>
                  <th className="py-3 px-3">Status</th>
                  <th className="py-3 px-3">Enrolled Date</th>
                  <th className="py-3 px-3">Positions</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/20">
                {users.map((u) => {
                  const isBlocked = !u.is_active;
                  return (
                    <tr key={u.id} className="hover:bg-white/[0.02] transition-colors">
                      <td className="py-3 px-4">
                        <div className="space-y-0.5">
                          <div className="font-bold text-white flex items-center gap-1.5 font-sans">
                            <span>{u.name}</span>
                            {u.is_admin && (
                              <span className="px-1.5 py-0.5 rounded text-[9px] bg-amber-500/10 border border-amber-500/30 text-amber-400">
                                ADMIN
                              </span>
                            )}
                          </div>
                          <div className="text-[11px] text-gray-400 font-mono">{u.email}</div>
                        </div>
                      </td>

                      <td className="py-3 px-3">
                        <span className="px-2 py-0.5 rounded-full text-[10px] uppercase font-bold bg-blue-500/10 border border-blue-500/20 text-blue-400">
                          {u.role || "user"}
                        </span>
                      </td>

                      <td className="py-3 px-3">
                        {u.face_enrolled ? (
                          <span className="text-emerald-400 flex items-center gap-1 text-[11px]">
                            <CheckCircle2 className="h-3.5 w-3.5" /> Enrolled
                          </span>
                        ) : (
                          <span className="text-gray-500 text-[11px]">None</span>
                        )}
                      </td>

                      <td className="py-3 px-3">
                        <button
                          onClick={() => handleToggleBlock(u)}
                          className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[10px] font-bold uppercase transition-all ${
                            u.is_active
                              ? "bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/20"
                              : "bg-red-500/10 border border-red-500/30 text-red-400 hover:bg-red-500/20"
                          }`}
                          title="Click to toggle block status"
                        >
                          {u.is_active ? <Unlock className="h-3 w-3" /> : <Lock className="h-3 w-3" />}
                          <span>{u.is_active ? "Active" : "Blocked"}</span>
                        </button>
                      </td>

                      <td className="py-3 px-3 text-gray-400">
                        {new Date(u.created_at).toLocaleDateString()}
                      </td>

                      <td className="py-3 px-3 text-gray-300 font-bold">
                        {u.positions_count} assets
                      </td>

                      <td className="py-3 px-4 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          <button
                            onClick={() => setShowEditUserModal(u)}
                            className="p-1.5 rounded-lg bg-background-elevated hover:bg-white/10 text-gray-400 hover:text-white transition-colors"
                            title="Edit user"
                          >
                            <Edit3 className="h-3.5 w-3.5" />
                          </button>
                          <button
                            onClick={() => handleToggleBlock(u)}
                            className={`p-1.5 rounded-lg transition-colors ${
                              u.is_active
                                ? "bg-amber-500/10 hover:bg-amber-500/20 text-amber-400"
                                : "bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400"
                            }`}
                            title={u.is_active ? "Block User" : "Unblock User"}
                          >
                            {u.is_active ? <UserX className="h-3.5 w-3.5" /> : <UserCheck className="h-3.5 w-3.5" />}
                          </button>
                          <button
                            onClick={() => setShowDeleteConfirm(u)}
                            className="p-1.5 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-400 transition-colors"
                            title="Delete User Permanently"
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}

                {users.length === 0 && (
                  <tr>
                    <td colSpan={7} className="py-8 text-center text-gray-500">
                      No user accounts found matching your query.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 2: DATA & FILE INGESTION */}
      {activeTab === "data" && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Uploader Card */}
          <div className="bg-[#0B0F19] border border-border rounded-2xl p-6 shadow-xl space-y-4">
            <div className="border-b border-border/50 pb-3">
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <Upload className="h-4 w-4 text-brand" /> Upload Market Data (CSV / JSON)
              </h2>
              <p className="text-xs text-gray-400">
                Upload historical OHLCV pricing datasets (e.g. PSX or Global equities) directly into the database.
              </p>
            </div>

            <form onSubmit={handleFileUpload} className="space-y-4 text-xs">
              <div className="space-y-1">
                <label className="text-[11px] text-gray-400 font-mono">Target Market</label>
                <select
                  value={targetMarket}
                  onChange={(e) => setTargetMarket(e.target.value)}
                  className="w-full bg-[#12192C] border border-border rounded-xl p-2.5 text-white"
                >
                  <option value="PK">Pakistan (PSX - PKR)</option>
                  <option value="US">United States (NASDAQ / NYSE - USD)</option>
                  <option value="UK">United Kingdom (LSE - GBP)</option>
                  <option value="JP">Japan (TSE - JPY)</option>
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-[11px] text-gray-400 font-mono">Dataset Target Table</label>
                <select
                  value={datasetType}
                  onChange={(e) => setDatasetType(e.target.value)}
                  className="w-full bg-[#12192C] border border-border rounded-xl p-2.5 text-white"
                >
                  <option value="historical_prices">Historical OHLCV Prices (market_data.price_data)</option>
                  <option value="securities_master">Security Master Registry (market_data.securities)</option>
                  <option value="raw_staging">Raw Staging Layer (market_data.raw_market_data)</option>
                </select>
              </div>

              <div className="border-2 border-dashed border-border/80 hover:border-brand/50 rounded-2xl p-6 text-center space-y-2 transition-colors cursor-pointer bg-[#070B14]">
                <input
                  type="file"
                  ref={fileInputRef}
                  accept=".csv,.json"
                  onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                  className="hidden"
                  id="admin-file-upload"
                />
                <label htmlFor="admin-file-upload" className="cursor-pointer block space-y-2">
                  <div className="w-10 h-10 rounded-full bg-brand/10 text-brand flex items-center justify-center mx-auto">
                    <FileText className="h-5 w-5" />
                  </div>
                  <div className="font-semibold text-white">
                    {uploadFile ? uploadFile.name : "Click to select CSV or JSON dataset"}
                  </div>
                  <div className="text-[10px] text-gray-500 font-mono">
                    {uploadFile ? `${(uploadFile.size / 1024).toFixed(1)} KB selected` : "Supports compiled_psx_historical_2017_2025.csv, yfinance exports"}
                  </div>
                </label>
              </div>

              {uploadResult && (
                <div className="p-3 rounded-xl bg-background-elevated border border-border font-mono text-[11px] text-gray-300">
                  {uploadResult}
                </div>
              )}

              <button
                type="submit"
                disabled={!uploadFile || uploading}
                className="w-full py-2.5 rounded-xl bg-brand hover:bg-brand-hover text-white font-bold flex items-center justify-center gap-2 disabled:opacity-50 transition-all shadow-md shadow-blue-500/20"
              >
                {uploading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
                <span>{uploading ? "Ingesting into Database…" : "Execute Dataset Ingestion"}</span>
              </button>
            </form>
          </div>

          {/* Purge & Maintenance Card */}
          <div className="bg-[#0B0F19] border border-border rounded-2xl p-6 shadow-xl space-y-4">
            <div className="border-b border-border/50 pb-3">
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <Trash2 className="h-4 w-4 text-red-400" /> Data Purging &amp; Database Maintenance
              </h2>
              <p className="text-xs text-gray-400">
                Purge test datasets, delete specific ticker price histories, or clear cache partitions.
              </p>
            </div>

            <div className="space-y-4 text-xs">
              <div className="space-y-1">
                <label className="text-[11px] text-gray-400 font-mono">Purge Specific Ticker History</label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    placeholder="Enter ticker (e.g. TEST, AAPL, ENGRO)..."
                    value={purgeTarget}
                    onChange={(e) => setPurgeTarget(e.target.value.toUpperCase())}
                    className="flex-1 bg-[#12192C] border border-border rounded-xl px-3 py-2 text-white font-mono"
                  />
                  <button
                    onClick={() => purgeTarget && handlePurge(purgeTarget)}
                    disabled={!purgeTarget || purging}
                    className="px-4 py-2 rounded-xl bg-red-500/10 hover:bg-red-500/20 border border-red-500/30 text-red-400 font-bold transition-all disabled:opacity-50"
                  >
                    Purge
                  </button>
                </div>
              </div>

              <div className="pt-3 border-t border-border/50 space-y-2">
                <div className="text-[11px] font-bold text-gray-300 font-mono">Quick Maintenance Tools</div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  <button
                    onClick={() => handlePurge("INGESTION_LOGS")}
                    className="p-3 rounded-xl bg-background-elevated hover:bg-white/5 border border-border text-left space-y-1 group transition-colors"
                  >
                    <div className="font-bold text-white group-hover:text-red-400 transition-colors">Clear Ingestion Logs</div>
                    <div className="text-[10px] text-gray-500">Purges background job execution records</div>
                  </button>

                  <button
                    onClick={() => handlePurge("RAW_STAGING")}
                    className="p-3 rounded-xl bg-background-elevated hover:bg-white/5 border border-border text-left space-y-1 group transition-colors"
                  >
                    <div className="font-bold text-white group-hover:text-amber-400 transition-colors">Purge Raw Staging</div>
                    <div className="text-[10px] text-gray-500">Frees temporary import buffer</div>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: AUDIT LOGS */}
      {activeTab === "audit" && (
        <div className="bg-[#0B0F19] border border-border rounded-2xl p-6 shadow-xl space-y-4">
          <div className="flex items-center justify-between border-b border-border/50 pb-3">
            <div>
              <h2 className="text-base font-bold text-white">System &amp; Security Audit Trail</h2>
              <p className="text-xs text-gray-400">Immutable ledger of administrative actions, data uploads, and security events.</p>
            </div>
            <span className="text-xs font-mono text-gray-500">{auditLogs.length} Events Tracked</span>
          </div>

          <div className="overflow-x-auto border border-border/60 rounded-xl">
            <table className="w-full text-xs font-mono text-left border-collapse">
              <thead>
                <tr className="bg-background-elevated border-b border-border/60 text-gray-400 text-[10px] uppercase">
                  <th className="py-3 px-4">Timestamp</th>
                  <th className="py-3 px-3">Action</th>
                  <th className="py-3 px-3">Target</th>
                  <th className="py-3 px-3">Actor</th>
                  <th className="py-3 px-3">Status</th>
                  <th className="py-3 px-4">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/20">
                {auditLogs.map((log) => (
                  <tr key={log.id} className="hover:bg-white/[0.02] transition-colors">
                    <td className="py-3 px-4 text-gray-400">{new Date(log.timestamp).toLocaleString()}</td>
                    <td className="py-3 px-3 font-bold text-white">{log.action}</td>
                    <td className="py-3 px-3 text-brand">{log.target_id || log.target_type}</td>
                    <td className="py-3 px-3 text-gray-400">{log.actor_email || "system"}</td>
                    <td className="py-3 px-3">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        {log.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-gray-400 max-w-xs truncate">{log.details}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* MODAL: ADD USER */}
      {showAddUserModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={() => setShowAddUserModal(false)} />
          <form
            onSubmit={handleCreateUser}
            className="relative bg-[#0E1422] border border-border rounded-2xl shadow-2xl w-full max-w-md p-6 space-y-4 text-xs z-10 font-sans"
          >
            <div className="flex items-center justify-between border-b border-border/50 pb-3">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <UserPlus className="h-4 w-4 text-brand" /> Create Database User Account
              </h3>
              <button type="button" onClick={() => setShowAddUserModal(false)} className="text-gray-500 hover:text-white">✕</button>
            </div>

            <div className="space-y-1">
              <label className="text-[11px] text-gray-400 font-mono">Full Name</label>
              <input
                type="text"
                value={newUserName}
                onChange={(e) => setNewUserName(e.target.value)}
                placeholder="e.g. Ahmad Asif"
                className="w-full bg-[#12192C] border border-border rounded-xl p-2.5 text-white"
                required
              />
            </div>

            <div className="space-y-1">
              <label className="text-[11px] text-gray-400 font-mono">Email Address</label>
              <input
                type="email"
                value={newUserEmail}
                onChange={(e) => setNewUserEmail(e.target.value)}
                placeholder="e.g. ahmad@stocksense.ai"
                className="w-full bg-[#12192C] border border-border rounded-xl p-2.5 text-white"
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <label className="text-[11px] text-gray-400 font-mono">Role</label>
                <select
                  value={newUserRole}
                  onChange={(e) => setNewUserRole(e.target.value)}
                  className="w-full bg-[#12192C] border border-border rounded-xl p-2.5 text-white"
                >
                  <option value="user">User (Standard)</option>
                  <option value="analyst">Analyst</option>
                  <option value="admin">Administrator</option>
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-[11px] text-gray-400 font-mono">Initial Status</label>
                <select
                  value={newUserActive ? "active" : "blocked"}
                  onChange={(e) => setNewUserActive(e.target.value === "active")}
                  className="w-full bg-[#12192C] border border-border rounded-xl p-2.5 text-white"
                >
                  <option value="active">Active</option>
                  <option value="blocked">Blocked</option>
                </select>
              </div>
            </div>

            <div className="pt-3 flex justify-end gap-2 border-t border-border/50">
              <button
                type="button"
                onClick={() => setShowAddUserModal(false)}
                className="px-4 py-2 rounded-xl bg-background-elevated border border-border text-gray-400 hover:text-white"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={creatingUser}
                className="px-4 py-2 rounded-xl bg-brand hover:bg-brand-hover text-white font-bold flex items-center gap-1.5"
              >
                {creatingUser ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <UserPlus className="h-3.5 w-3.5" />}
                <span>Create User</span>
              </button>
            </div>
          </form>
        </div>
      )}

      {/* MODAL: EDIT USER */}
      {showEditUserModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={() => setShowEditUserModal(null)} />
          <form
            onSubmit={handleUpdateUser}
            className="relative bg-[#0E1422] border border-border rounded-2xl shadow-2xl w-full max-w-md p-6 space-y-4 text-xs z-10 font-sans"
          >
            <div className="flex items-center justify-between border-b border-border/50 pb-3">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Edit3 className="h-4 w-4 text-brand" /> Edit User: {showEditUserModal.name}
              </h3>
              <button type="button" onClick={() => setShowEditUserModal(null)} className="text-gray-500 hover:text-white">✕</button>
            </div>

            <div className="space-y-1">
              <label className="text-[11px] text-gray-400 font-mono">Full Name</label>
              <input
                type="text"
                value={showEditUserModal.name}
                onChange={(e) => setShowEditUserModal({ ...showEditUserModal, name: e.target.value })}
                className="w-full bg-[#12192C] border border-border rounded-xl p-2.5 text-white"
                required
              />
            </div>

            <div className="space-y-1">
              <label className="text-[11px] text-gray-400 font-mono">Email Address</label>
              <input
                type="email"
                value={showEditUserModal.email}
                onChange={(e) => setShowEditUserModal({ ...showEditUserModal, email: e.target.value })}
                className="w-full bg-[#12192C] border border-border rounded-xl p-2.5 text-white"
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <label className="text-[11px] text-gray-400 font-mono">Role</label>
                <select
                  value={showEditUserModal.role}
                  onChange={(e) => setShowEditUserModal({ ...showEditUserModal, role: e.target.value })}
                  className="w-full bg-[#12192C] border border-border rounded-xl p-2.5 text-white"
                >
                  <option value="user">User</option>
                  <option value="analyst">Analyst</option>
                  <option value="admin">Administrator</option>
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-[11px] text-gray-400 font-mono">Status</label>
                <select
                  value={showEditUserModal.is_active ? "active" : "blocked"}
                  onChange={(e) => setShowEditUserModal({ ...showEditUserModal, is_active: e.target.value === "active" })}
                  className="w-full bg-[#12192C] border border-border rounded-xl p-2.5 text-white"
                >
                  <option value="active">Active</option>
                  <option value="blocked">Blocked</option>
                </select>
              </div>
            </div>

            <div className="pt-3 flex justify-end gap-2 border-t border-border/50">
              <button
                type="button"
                onClick={() => setShowEditUserModal(null)}
                className="px-4 py-2 rounded-xl bg-background-elevated border border-border text-gray-400 hover:text-white"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 rounded-xl bg-brand hover:bg-brand-hover text-white font-bold"
              >
                Save Changes
              </button>
            </div>
          </form>
        </div>
      )}

      {/* MODAL: DELETE CONFIRMATION */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/75 backdrop-blur-sm" onClick={() => setShowDeleteConfirm(null)} />
          <div className="relative bg-[#0E1422] border border-red-500/40 rounded-2xl shadow-2xl w-full max-w-md p-6 space-y-4 text-xs z-10 font-sans">
            <div className="flex items-center gap-3 text-red-400">
              <div className="p-2 rounded-xl bg-red-500/10 border border-red-500/20">
                <AlertTriangle className="h-6 w-6" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white">Permanently Delete User?</h3>
                <p className="text-xs text-gray-400">This action cannot be undone.</p>
              </div>
            </div>

            <div className="p-3 bg-red-500/5 border border-red-500/20 rounded-xl space-y-1 font-mono text-[11px] text-gray-300">
              <div>User: <span className="text-white font-bold">{showDeleteConfirm.name}</span> ({showDeleteConfirm.email})</div>
              <div>Will permanently remove user account, all tracked positions, watchlists, and biometrics from database.</div>
            </div>

            <div className="pt-2 flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setShowDeleteConfirm(null)}
                className="px-4 py-2 rounded-xl bg-background-elevated border border-border text-gray-300 hover:text-white"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => handleDeleteUser(showDeleteConfirm)}
                className="px-4 py-2 rounded-xl bg-red-600 hover:bg-red-700 text-white font-bold flex items-center gap-1.5 shadow-lg shadow-red-600/20"
              >
                <Trash2 className="h-3.5 w-3.5" />
                <span>Delete Permanently</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
