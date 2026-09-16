import { useEffect, useState } from 'react'
import { Activity, AlertTriangle, BarChart3, Bell, BellRing, Bot, Car, ChevronRight, ClipboardList, DollarSign, FileText, Gauge, Lock, LogOut, Package, Plus, RefreshCw, Search, Settings, ShieldCheck, ShoppingCart, Sparkles, TrendingDown, TrendingUp, Trash2, Truck, Unlock, UploadCloud, Users, Wallet, Wrench, X } from 'lucide-react'
import {
  addCashMovement, adjustStockItem, anonymizeCustomer, anonymizeInactiveCustomers, Appointment, askAI, AuditLog,
  cancelAppointment, cancelFinanceEntry, cancelPurchaseOrder, cancelWorkOrder, CashMovement, CashSession,
  closeCashSession, closeWorkOrder, createAppointment, createCustomer, createFinanceEntry, createPurchaseOrder,
  createStockItem, createSupplier, createWorkOrder, Customer, CustomerListItem, DashboardReport, exportCustomerData,
  FinanceEntry, getCurrentCashSession, getCustomer, getDashboardReport, ingestFile, listAppointments, listAuditLogs,
  listCashMovements, listCustomers, listFinanceEntries, listNotificationQueue, listPurchaseOrders,
  listRetentionCandidates, listStock, listSuppliers, listWorkOrders, login, logout, me,
  NotificationQueueEntry, openCashSession, payFinanceEntry, processNotificationQueue, purgeOldNotifications,
  PurchaseOrder, receivePurchaseOrder, RetentionCandidate, StockItem, Supplier, WorkOrder,
} from './lib/api'

type Page = 'dashboard' | 'customers' | 'agenda' | 'stock' | 'workorders' | 'reports' | 'finance' | 'purchases' | 'audit' | 'retention' | 'notifqueue'

const nav: [string, any, Page][] = [
  ['Dashboard', Gauge, 'dashboard'], ['Agenda', Bell, 'agenda'], ['Clientes', Users, 'customers'],
  ['Veículos', Car, 'dashboard'], ['Ordens de serviço', Wrench, 'workorders'],
  ['Estoque', Package, 'stock'], ['Compras', ShoppingCart, 'purchases'], ['Financeiro', DollarSign, 'finance'],
  ['Relatórios', BarChart3, 'reports'], ['Auditoria', ClipboardList, 'audit'], ['Retenção', ShieldCheck, 'retention'],
  ['Fila de notificações', BellRing, 'notifqueue'], ['Documentos RAG', FileText, 'dashboard'],
]

const pageEyebrow: Record<Page, string> = {
  dashboard: 'Visão geral', customers: 'Cadastro', agenda: 'Operação',
  stock: 'Suprimentos', workorders: 'Operação', reports: 'Indicadores', finance: 'Financeiro', purchases: 'Suprimentos',
  audit: 'Governança', retention: 'Governança', notifqueue: 'Comunicação',
}
const pageTitle: Record<Page, string> = {
  dashboard: 'Central da oficina', customers: 'Clientes', agenda: 'Agenda',

  stock: 'Estoque', workorders: 'Ordens de serviço', reports: 'Relatórios', finance: 'Financeiro & Caixa',
  purchases: 'Compras & Fornecedores', audit: 'Auditoria', retention: 'Retenção de dados',
  notifqueue: 'Fila de notificações',
}

function LoginScreen({ onLoggedIn }: { onLoggedIn: () => void }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setBusy(true); setError('')
    try {
      await login(email, password)
      onLoggedIn()
    } catch {
      setError('E-mail ou senha inválidos.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="grid min-h-screen place-items-center bg-[#f6f8fb] p-5">
      <form onSubmit={handleSubmit} className="w-full max-w-sm rounded-3xl border border-slate-200 bg-white p-8 shadow-soft">
        <div className="mb-6 flex items-center gap-3">
          <div className="grid h-10 w-10 place-items-center rounded-2xl bg-slate-950 text-white"><Wrench size={19}/></div>
          <div><div className="font-black tracking-tight">Oficina AI</div><div className="text-xs text-slate-400">Entrar</div></div>
        </div>
        <label className="mb-3 block text-sm">
          <span className="mb-1 block text-slate-600">E-mail</span>
          <input value={email} onChange={e=>setEmail(e.target.value)} type="text" required
            className="w-full rounded-xl border border-slate-200 px-3 py-2.5 outline-none focus:border-slate-400"/>
        </label>
        <label className="mb-4 block text-sm">
          <span className="mb-1 block text-slate-600">Senha</span>
          <input value={password} onChange={e=>setPassword(e.target.value)} type="password" required
            className="w-full rounded-xl border border-slate-200 px-3 py-2.5 outline-none focus:border-slate-400"/>
        </label>
        {error && <div className="mb-4 rounded-xl bg-red-50 px-3 py-2 text-sm text-red-600">{error}</div>}
        <button disabled={busy} className="w-full rounded-xl bg-slate-950 px-4 py-2.5 text-sm font-bold text-white disabled:opacity-50">
          {busy ? 'Entrando...' : 'Entrar'}
        </button>
      </form>
    </div>
  )
}

function NewCustomerModal({ onClose, onCreated }: { onClose: () => void; onCreated: (c: Customer) => void }) {
  const [name, setName] = useState('')
  const [docNumber, setDocNumber] = useState('')
  const [phone, setPhone] = useState('')
  const [plate, setPlate] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setBusy(true); setError('')
    try {
      const created = await createCustomer({
        name, document: docNumber, phone,
        vehicles: plate.trim() ? [{ plate: plate.trim() }] : [],
      })
      onCreated(created)
      onClose()
    } catch (e: any) {
      setError('Não foi possível salvar. Confira os dados (documento/placa podem já estar em uso).')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="fixed inset-0 z-20 grid place-items-center bg-slate-950/40 p-5" onClick={onClose}>
      <form onSubmit={handleSubmit} onClick={e => e.stopPropagation()}
        className="w-full max-w-md rounded-3xl border border-slate-200 bg-white p-6 shadow-soft">
        <div className="mb-5 flex items-center justify-between">
          <h2 className="font-black">Novo cliente</h2>
          <button type="button" onClick={onClose} className="rounded-lg p-1 text-slate-400 hover:bg-slate-100"><X size={18}/></button>
        </div>
        <label className="mb-3 block text-sm">
          <span className="mb-1 block text-slate-600">Nome *</span>
          <input value={name} onChange={e=>setName(e.target.value)} required
            className="w-full rounded-xl border border-slate-200 px-3 py-2.5 outline-none focus:border-slate-400"/>
        </label>
        <div className="mb-3 grid grid-cols-2 gap-3">
          <label className="block text-sm">
            <span className="mb-1 block text-slate-600">CPF/CNPJ</span>
            <input value={docNumber} onChange={e=>setDocNumber(e.target.value)}
              className="w-full rounded-xl border border-slate-200 px-3 py-2.5 outline-none focus:border-slate-400"/>
          </label>
          <label className="block text-sm">
            <span className="mb-1 block text-slate-600">Telefone</span>
            <input value={phone} onChange={e=>setPhone(e.target.value)}
              className="w-full rounded-xl border border-slate-200 px-3 py-2.5 outline-none focus:border-slate-400"/>
          </label>
        </div>
        <label className="mb-4 block text-sm">
          <span className="mb-1 block text-slate-600">Placa do veículo (opcional)</span>
          <input value={plate} onChange={e=>setPlate(e.target.value)} placeholder="ABC1234"
            className="w-full rounded-xl border border-slate-200 px-3 py-2.5 outline-none focus:border-slate-400"/>
        </label>
        {error && <div className="mb-4 rounded-xl bg-red-50 px-3 py-2 text-sm text-red-600">{error}</div>}
        <button disabled={busy} className="w-full rounded-xl bg-slate-950 px-4 py-2.5 text-sm font-bold text-white disabled:opacity-50">
          {busy ? 'Salvando...' : 'Salvar cliente'}
        </button>
      </form>
    </div>
  )
}

function CustomersPage() {
  const [items, setItems] = useState<CustomerListItem[]>([])
  const [q, setQ] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [actionError, setActionError] = useState('')
  const [showNew, setShowNew] = useState(false)
  const [busyId, setBusyId] = useState<number | null>(null)

  function reload(query?: string) {
    setLoading(true); setError('')
    listCustomers(query)
      .then(setItems)
      .catch(() => setError('Não foi possível carregar os clientes.'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { reload() }, [])

  async function handleExport(id: number, name: string) {
    setBusyId(id); setActionError('')
    try {
      const data = await exportCustomerData(id)
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `cliente-${id}-${name.replace(/\s+/g, '-').toLowerCase()}.json`
      a.click()
      URL.revokeObjectURL(url)
    } catch {
      setActionError('Não foi possível exportar os dados deste cliente.')
    } finally {
      setBusyId(null)
    }
  }

  async function handleAnonymize(id: number) {
    if (!window.confirm('Anonimizar este cliente? Nome, documento, telefone e e-mail serão apagados permanentemente. Esta ação não pode ser desfeita.')) return
    setBusyId(id); setActionError('')
    try {
      await anonymizeCustomer(id)
      reload(q)
    } catch {
      setActionError('Não foi possível anonimizar este cliente.')
    } finally {
      setBusyId(null)
    }
  }

  return (
    <section className="mx-auto max-w-7xl space-y-6 p-5 md:p-8">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <div className="text-xs font-semibold uppercase tracking-[.18em] text-slate-400">Cadastro</div>
          <h1 className="text-xl font-black">Clientes</h1>
        </div>
        <div className="flex gap-2">
          <div className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2">
            <Search size={16} className="text-slate-400"/>
            <input value={q} onChange={e=>setQ(e.target.value)}
              onKeyDown={e=>{if(e.key==='Enter') reload(q)}}
              placeholder="Buscar por nome, documento, telefone..."
              className="w-64 bg-transparent text-sm outline-none"/>
          </div>
          <button onClick={()=>setShowNew(true)}
            className="flex items-center gap-2 rounded-xl bg-slate-950 px-4 py-2 text-sm font-bold text-white">
            <Plus size={16}/> Novo cliente
          </button>
        </div>
      </div>

      {actionError && <div className="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-600">{actionError}</div>}

      <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-soft">
        {loading && <div className="p-6 text-sm text-slate-400">Carregando...</div>}
        {error && <div className="p-6 text-sm text-red-600">{error}</div>}
        {!loading && !error && items.length === 0 && (
          <div className="p-6 text-sm text-slate-400">Nenhum cliente encontrado.</div>
        )}
        {!loading && !error && items.length > 0 && (
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-left text-xs font-bold uppercase tracking-wider text-slate-400">
              <tr>
                <th className="px-5 py-3">Nome</th><th className="px-5 py-3">Documento</th>
                <th className="px-5 py-3">Telefone</th><th className="px-5 py-3">Veículos</th>
                <th className="px-5 py-3">Status</th><th className="px-5 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {items.map(c => (
                <tr key={c.id} className="border-t border-slate-100">
                  <td className="px-5 py-3 font-semibold">{c.name}</td>
                  <td className="px-5 py-3 text-slate-500">{c.document || '—'}</td>
                  <td className="px-5 py-3 text-slate-500">{c.phone || '—'}</td>
                  <td className="px-5 py-3 text-slate-500">{c.vehicle_count}</td>
                  <td className="px-5 py-3">
                    <span className={`rounded-full px-2.5 py-1 text-xs font-bold ${c.is_active ? 'bg-emerald-50 text-emerald-600' : 'bg-slate-100 text-slate-400'}`}>
                      {c.is_active ? 'Ativo' : 'Inativo'}
                    </span>
                    {c.is_anonymized && (
                      <span className="ml-2 rounded-full bg-slate-100 px-2.5 py-1 text-xs font-bold text-slate-400">Anonimizado</span>
                    )}
                  </td>
                  <td className="px-5 py-3 text-right">
                    {!c.is_anonymized && (
                      <div className="flex justify-end gap-3">
                        <button disabled={busyId===c.id} onClick={()=>handleExport(c.id, c.name)} className="text-xs font-bold text-slate-600 hover:underline disabled:opacity-50">
                          Exportar dados
                        </button>
                        <button disabled={busyId===c.id} onClick={()=>handleAnonymize(c.id)} className="text-xs font-bold text-red-500 hover:underline disabled:opacity-50">
                          Anonimizar
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {showNew && (
        <NewCustomerModal onClose={()=>setShowNew(false)} onCreated={()=>reload(q)} />
      )}
    </section>
  )
}

function NewAppointmentModal({ onClose, onCreated }: { onClose: () => void; onCreated: (a: Appointment) => void }) {
  const [customerQuery, setCustomerQuery] = useState('')
  const [customerResults, setCustomerResults] = useState<CustomerListItem[]>([])
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null)
  const [vehicleId, setVehicleId] = useState<number | ''>('')
  const [date, setDate] = useState('')
  const [time, setTime] = useState('09:00')
  const [duration, setDuration] = useState(60)
  const [serviceType, setServiceType] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    if (!customerQuery.trim()) { setCustomerResults([]); return }
    const timeout = setTimeout(() => {
      listCustomers(customerQuery).then(setCustomerResults).catch(() => setCustomerResults([]))
    }, 300)
    return () => clearTimeout(timeout)
  }, [customerQuery])

  async function pickCustomer(id: number) {
    const full = await getCustomer(id)
    setSelectedCustomer(full)
    setVehicleId(full.vehicles[0]?.id ?? '')
    setCustomerResults([])
    setCustomerQuery(full.name)
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!selectedCustomer || !date) { setError('Selecione um cliente e uma data.'); return }
    setBusy(true); setError('')
    try {
      const scheduledAt = new Date(`${date}T${time}:00`).toISOString()
      const created = await createAppointment({
        customer_id: selectedCustomer.id,
        vehicle_id: vehicleId === '' ? undefined : Number(vehicleId),
        scheduled_at: scheduledAt,
        duration_minutes: duration,
        service_type: serviceType,
      })
      onCreated(created)
      onClose()
    } catch (e: any) {
      setError('Não foi possível agendar. Pode haver conflito de horário — confira e tente de novo.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="fixed inset-0 z-20 grid place-items-center bg-slate-950/40 p-5" onClick={onClose}>
      <form onSubmit={handleSubmit} onClick={e => e.stopPropagation()}
        className="w-full max-w-md rounded-3xl border border-slate-200 bg-white p-6 shadow-soft">
        <div className="mb-5 flex items-center justify-between">
          <h2 className="font-black">Novo agendamento</h2>
          <button type="button" onClick={onClose} className="rounded-lg p-1 text-slate-400 hover:bg-slate-100"><X size={18}/></button>
        </div>

        <label className="relative mb-3 block text-sm">
          <span className="mb-1 block text-slate-600">Cliente *</span>
          <input value={customerQuery}
            onChange={e => { setCustomerQuery(e.target.value); setSelectedCustomer(null) }}
            placeholder="Buscar cliente por nome..."
            className="w-full rounded-xl border border-slate-200 px-3 py-2.5 outline-none focus:border-slate-400"/>
          {customerResults.length > 0 && (
            <div className="absolute z-10 mt-1 max-h-40 w-full overflow-auto rounded-xl border border-slate-200 bg-white shadow-soft">
              {customerResults.map(c => (
                <button key={c.id} type="button" onClick={() => pickCustomer(c.id)}
                  className="block w-full px-3 py-2 text-left text-sm hover:bg-slate-50">
                  {c.name} {c.phone && <span className="text-slate-400">· {c.phone}</span>}
                </button>
              ))}
            </div>
          )}
        </label>

        {selectedCustomer && selectedCustomer.vehicles.length > 0 && (
          <label className="mb-3 block text-sm">
            <span className="mb-1 block text-slate-600">Veículo</span>
            <select value={vehicleId} onChange={e => setVehicleId(e.target.value ? Number(e.target.value) : '')}
              className="w-full rounded-xl border border-slate-200 px-3 py-2.5 outline-none focus:border-slate-400">
              <option value="">Sem veículo definido</option>
              {selectedCustomer.vehicles.map(v => (
                <option key={v.id} value={v.id}>{v.plate} {v.brand ? `· ${v.brand} ${v.model}` : ''}</option>
              ))}
            </select>
          </label>
        )}

        <div className="mb-3 grid grid-cols-2 gap-3">
          <label className="block text-sm">
            <span className="mb-1 block text-slate-600">Data *</span>
            <input type="date" value={date} onChange={e=>setDate(e.target.value)} required
              className="w-full rounded-xl border border-slate-200 px-3 py-2.5 outline-none focus:border-slate-400"/>
          </label>
          <label className="block text-sm">
            <span className="mb-1 block text-slate-600">Hora *</span>
            <input type="time" value={time} onChange={e=>setTime(e.target.value)} required
              className="w-full rounded-xl border border-slate-200 px-3 py-2.5 outline-none focus:border-slate-400"/>
          </label>
        </div>

        <div className="mb-3 grid grid-cols-2 gap-3">
          <label className="block text-sm">
            <span className="mb-1 block text-slate-600">Duração (min)</span>
            <input type="number" min={15} max={480} step={15} value={duration}
              onChange={e=>setDuration(Number(e.target.value))}
              className="w-full rounded-xl border border-slate-200 px-3 py-2.5 outline-none focus:border-slate-400"/>
          </label>
          <label className="block text-sm">
            <span className="mb-1 block text-slate-600">Serviço</span>
            <input value={serviceType} onChange={e=>setServiceType(e.target.value)} placeholder="Ex.: Revisão"
              className="w-full rounded-xl border border-slate-200 px-3 py-2.5 outline-none focus:border-slate-400"/>
          </label>
        </div>

        {error && <div className="mb-4 rounded-xl bg-red-50 px-3 py-2 text-sm text-red-600">{error}</div>}
        <button disabled={busy} className="w-full rounded-xl bg-slate-950 px-4 py-2.5 text-sm font-bold text-white disabled:opacity-50">
          {busy ? 'Agendando...' : 'Agendar'}
        </button>
      </form>
    </div>
  )
}

const statusLabel: Record<Appointment['status'], string> = {
  SCHEDULED: 'Agendado', CONFIRMED: 'Confirmado', IN_PROGRESS: 'Em andamento',
  DONE: 'Concluído', CANCELLED: 'Cancelado', NO_SHOW: 'Não compareceu',
}
const statusColor: Record<Appointment['status'], string> = {
  SCHEDULED: 'bg-blue-50 text-blue-600', CONFIRMED: 'bg-emerald-50 text-emerald-600',
  IN_PROGRESS: 'bg-amber-50 text-amber-600', DONE: 'bg-slate-100 text-slate-500',
  CANCELLED: 'bg-red-50 text-red-500', NO_SHOW: 'bg-red-50 text-red-500',
}

function AgendaPage() {
  const [items, setItems] = useState<Appointment[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showNew, setShowNew] = useState(false)

  function reload() {
    setLoading(true); setError('')
    listAppointments()
      .then(setItems)
      .catch(() => setError('Não foi possível carregar a agenda.'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { reload() }, [])

  async function handleCancel(id: number) {
    try {
      await cancelAppointment(id)
      reload()
    } catch { /* silencioso: item permanece como está na lista */ }
  }

  return (
    <section className="mx-auto max-w-7xl space-y-6 p-5 md:p-8">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <div className="text-xs font-semibold uppercase tracking-[.18em] text-slate-400">Operação</div>
          <h1 className="text-xl font-black">Agenda</h1>
        </div>
        <button onClick={()=>setShowNew(true)}
          className="flex items-center gap-2 rounded-xl bg-slate-950 px-4 py-2 text-sm font-bold text-white">
          <Plus size={16}/> Novo agendamento
        </button>
      </div>

      <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-soft">
        {loading && <div className="p-6 text-sm text-slate-400">Carregando...</div>}
        {error && <div className="p-6 text-sm text-red-600">{error}</div>}
        {!loading && !error && items.length === 0 && (
          <div className="p-6 text-sm text-slate-400">Nenhum agendamento encontrado.</div>
        )}
        {!loading && !error && items.length > 0 && (
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-left text-xs font-bold uppercase tracking-wider text-slate-400">
              <tr>
                <th className="px-5 py-3">Quando</th><th className="px-5 py-3">Cliente</th>
                <th className="px-5 py-3">Veículo</th><th className="px-5 py-3">Serviço</th>
                <th className="px-5 py-3">Status</th><th className="px-5 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {items.map(a => (
                <tr key={a.id} className="border-t border-slate-100">
                  <td className="px-5 py-3 font-semibold">
                    {new Date(a.scheduled_at).toLocaleString('pt-BR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })}
                  </td>
                  <td className="px-5 py-3 text-slate-500">{a.customer_name}</td>
                  <td className="px-5 py-3 text-slate-500">{a.vehicle_plate || '—'}</td>
                  <td className="px-5 py-3 text-slate-500">{a.service_type || '—'}</td>
                  <td className="px-5 py-3">
                    <span className={`rounded-full px-2.5 py-1 text-xs font-bold ${statusColor[a.status]}`}>
                      {statusLabel[a.status]}
                    </span>
                  </td>
                  <td className="px-5 py-3 text-right">
                    {(a.status === 'SCHEDULED' || a.status === 'CONFIRMED') && (
                      <button onClick={() => handleCancel(a.id)} className="text-xs font-bold text-red-500 hover:underline">
                        Cancelar
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {showNew && (
        <NewAppointmentModal onClose={()=>setShowNew(false)} onCreated={reload} />
      )}
    </section>
  )
}

function NewStockItemModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [sku, setSku] = useState('')
  const [name, setName] = useState('')
  const [unit, setUnit] = useState('un')
  const [quantity, setQuantity] = useState(0)
  const [minQuantity, setMinQuantity] = useState(0)
  const [costPrice, setCostPrice] = useState(0)
  const [salePrice, setSalePrice] = useState(0)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setBusy(true); setError('')
    try {
      await createStockItem({ sku, name, unit, quantity, min_quantity: minQuantity, cost_price: costPrice, sale_price: salePrice })
      onCreated()
      onClose()
    } catch {
      setError('Não foi possível salvar. O SKU pode já estar em uso.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="fixed inset-0 z-20 grid place-items-center bg-slate-950/40 p-5" onClick={onClose}>
      <form onSubmit={handleSubmit} onClick={e => e.stopPropagation()}
        className="w-full max-w-md rounded-3xl border border-slate-200 bg-white p-6 shadow-soft">
        <div className="mb-5 flex items-center justify-between">
          <h2 className="font-black">Novo item de estoque</h2>
          <button type="button" onClick={onClose} className="rounded-lg p-1 text-slate-400 hover:bg-slate-100"><X size={18}/></button>
        </div>
        <div className="mb-3 grid grid-cols-2 gap-3">
          <label className="block text-sm">
            <span className="mb-1 block text-slate-600">SKU *</span>
            <input value={sku} onChange={e=>setSku(e.target.value)} required
              className="w-full rounded-xl border border-slate-200 px-3 py-2.5 outline-none focus:border-slate-400"/>
          </label>
          <label className="block text-sm">
            <span className="mb-1 block text-slate-600">Unidade</span>
            <input value={unit} onChange={e=>setUnit(e.target.value)} placeholder="un, l, kg..."
              className="w-full rounded-xl border border-slate-200 px-3 py-2.5 outline-none focus:border-slate-400"/>
          </label>
        </div>
        <label className="mb-3 block text-sm">
          <span className="mb-1 block text-slate-600">Nome *</span>
          <input value={name} onChange={e=>setName(e.target.value)} required
            className="w-full rounded-xl border border-slate-200 px-3 py-2.5 outline-none focus:border-slate-400"/>
        </label>
        <div className="mb-3 grid grid-cols-2 gap-3">
          <label className="block text-sm">
            <span className="mb-1 block text-slate-600">Quantidade inicial</span>
            <input type="number" min={0} value={quantity} onChange={e=>setQuantity(Number(e.target.value))}
              className="w-full rounded-xl border border-slate-200 px-3 py-2.5 outline-none focus:border-slate-400"/>
          </label>
          <label className="block text-sm">
            <span className="mb-1 block text-slate-600">Estoque mínimo</span>
            <input type="number" min={0} value={minQuantity} onChange={e=>setMinQuantity(Number(e.target.value))}
              className="w-full rounded-xl border border-slate-200 px-3 py-2.5 outline-none focus:border-slate-400"/>
          </label>
        </div>
        <div className="mb-4 grid grid-cols-2 gap-3">
          <label className="block text-sm">
            <span className="mb-1 block text-slate-600">Preço de custo (R$)</span>
            <input type="number" min={0} step="0.01" value={costPrice} onChange={e=>setCostPrice(Number(e.target.value))}
              className="w-full rounded-xl border border-slate-200 px-3 py-2.5 outline-none focus:border-slate-400"/>
          </label>
          <label className="block text-sm">
            <span className="mb-1 block text-slate-600">Preço de venda (R$)</span>
            <input type="number" min={0} step="0.01" value={salePrice} onChange={e=>setSalePrice(Number(e.target.value))}
              className="w-full rounded-xl border border-slate-200 px-3 py-2.5 outline-none focus:border-slate-400"/>
          </label>
        </div>
        {error && <div className="mb-4 rounded-xl bg-red-50 px-3 py-2 text-sm text-red-600">{error}</div>}
        <button disabled={busy} className="w-full rounded-xl bg-slate-950 px-4 py-2.5 text-sm font-bold text-white disabled:opacity-50">
          {busy ? 'Salvando...' : 'Salvar item'}
        </button>
      </form>
    </div>
  )
}

function AdjustStockModal({ item, onClose, onAdjusted }: { item: StockItem; onClose: () => void; onAdjusted: () => void }) {
  const [type, setType] = useState<'IN' | 'OUT' | 'ADJUSTMENT'>('IN')
  const [quantity, setQuantity] = useState(1)
  const [reason, setReason] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setBusy(true); setError('')
    try {
      await adjustStockItem(item.id, { type, quantity, reason })
      onAdjusted()
      onClose()
    } catch {
      setError('Não foi possível ajustar. Confira se há saldo suficiente para uma saída.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="fixed inset-0 z-20 grid place-items-center bg-slate-950/40 p-5" onClick={onClose}>
      <form onSubmit={handleSubmit} onClick={e => e.stopPropagation()}
        className="w-full max-w-sm rounded-3xl border border-slate-200 bg-white p-6 shadow-soft">
        <div className="mb-5 flex items-center justify-between">
          <h2 className="font-black">Ajustar estoque</h2>
          <button type="button" onClick={onClose} className="rounded-lg p-1 text-slate-400 hover:bg-slate-100"><X size={18}/></button>
        </div>
        <p className="mb-4 text-sm text-slate-500">{item.name} · saldo atual: <b>{item.quantity} {item.unit}</b></p>
        <label className="mb-3 block text-sm">
          <span className="mb-1 block text-slate-600">Tipo de movimento</span>
          <select value={type} onChange={e=>setType(e.target.value as any)}
            className="w-full rounded-xl border border-slate-200 px-3 py-2.5 outline-none focus:border-slate-400">
            <option value="IN">Entrada</option>
            <option value="OUT">Saída</option>
            <option value="ADJUSTMENT">Ajuste de contagem</option>
          </select>
        </label>
        <label className="mb-3 block text-sm">
          <span className="mb-1 block text-slate-600">Quantidade</span>
          <input type="number" min={1} value={quantity} onChange={e=>setQuantity(Number(e.target.value))} required
            className="w-full rounded-xl border border-slate-200 px-3 py-2.5 outline-none focus:border-slate-400"/>
        </label>
        <label className="mb-4 block text-sm">
          <span className="mb-1 block text-slate-600">Motivo</span>
          <input value={reason} onChange={e=>setReason(e.target.value)} placeholder="Ex.: reposição do fornecedor"
            className="w-full rounded-xl border border-slate-200 px-3 py-2.5 outline-none focus:border-slate-400"/>
        </label>
        {error && <div className="mb-4 rounded-xl bg-red-50 px-3 py-2 text-sm text-red-600">{error}</div>}
        <button disabled={busy} className="w-full rounded-xl bg-slate-950 px-4 py-2.5 text-sm font-bold text-white disabled:opacity-50">
          {busy ? 'Salvando...' : 'Confirmar ajuste'}
        </button>
      </form>
    </div>
  )
}

function StockPage() {
  const [items, setItems] = useState<StockItem[]>([])
  const [q, setQ] = useState('')
  const [onlyLow, setOnlyLow] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showNew, setShowNew] = useState(false)
  const [adjustTarget, setAdjustTarget] = useState<StockItem | null>(null)

  function reload() {
    setLoading(true); setError('')
    listStock({ q: q || undefined, onlyLowStock: onlyLow })
      .then(setItems)
      .catch(() => setError('Não foi possível carregar o estoque.'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { reload() }, [onlyLow])

  return (
    <section className="mx-auto max-w-7xl space-y-6 p-5 md:p-8">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <div className="text-xs font-semibold uppercase tracking-[.18em] text-slate-400">Suprimentos</div>
          <h1 className="text-xl font-black">Estoque</h1>
        </div>
        <div className="flex flex-wrap gap-2">
          <div className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2">
            <Search size={16} className="text-slate-400"/>
            <input value={q} onChange={e=>setQ(e.target.value)}
              onKeyDown={e=>{if(e.key==='Enter') reload()}}
              placeholder="Buscar por SKU ou nome..."
              className="w-56 bg-transparent text-sm outline-none"/>
          </div>
          <button onClick={()=>{setOnlyLow(v=>!v)}}
            className={`flex items-center gap-2 rounded-xl border px-3 py-2 text-sm font-bold ${onlyLow ? 'border-amber-200 bg-amber-50 text-amber-600' : 'border-slate-200 bg-white text-slate-600'}`}>
            <AlertTriangle size={16}/> Estoque crítico
          </button>
          <button onClick={()=>setShowNew(true)}
            className="flex items-center gap-2 rounded-xl bg-slate-950 px-4 py-2 text-sm font-bold text-white">
            <Plus size={16}/> Novo item
          </button>
        </div>
      </div>

      <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-soft">
        {loading && <div className="p-6 text-sm text-slate-400">Carregando...</div>}
        {error && <div className="p-6 text-sm text-red-600">{error}</div>}
        {!loading && !error && items.length === 0 && (
          <div className="p-6 text-sm text-slate-400">Nenhum item encontrado.</div>
        )}
        {!loading && !error && items.length > 0 && (
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-left text-xs font-bold uppercase tracking-wider text-slate-400">
              <tr>
                <th className="px-5 py-3">SKU</th><th className="px-5 py-3">Nome</th>
                <th className="px-5 py-3">Saldo</th><th className="px-5 py-3">Mínimo</th>
                <th className="px-5 py-3">Preço venda</th><th className="px-5 py-3">Status</th><th className="px-5 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {items.map(i => (
                <tr key={i.id} className="border-t border-slate-100">
                  <td className="px-5 py-3 font-mono text-xs text-slate-500">{i.sku}</td>
                  <td className="px-5 py-3 font-semibold">{i.name}</td>
                  <td className="px-5 py-3 text-slate-500">{i.quantity} {i.unit}</td>
                  <td className="px-5 py-3 text-slate-500">{i.min_quantity} {i.unit}</td>
                  <td className="px-5 py-3 text-slate-500">R$ {i.sale_price.toFixed(2)}</td>
                  <td className="px-5 py-3">
                    <span className={`rounded-full px-2.5 py-1 text-xs font-bold ${i.is_low_stock ? 'bg-amber-50 text-amber-600' : 'bg-emerald-50 text-emerald-600'}`}>
                      {i.is_low_stock ? 'Crítico' : 'OK'}
                    </span>
                  </td>
                  <td className="px-5 py-3 text-right">
                    <button onClick={() => setAdjustTarget(i)} className="text-xs font-bold text-slate-600 hover:underline">
                      Ajustar
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {showNew && <NewStockItemModal onClose={()=>setShowNew(false)} onCreated={reload} />}
      {adjustTarget && (
        <AdjustStockModal item={adjustTarget} onClose={()=>setAdjustTarget(null)} onAdjusted={reload} />
      )}
    </section>
  )
}

const workOrderStatusLabel: Record<string, string> = {
  OPEN: 'Aberta', IN_PROGRESS: 'Em andamento', AWAITING_APPROVAL: 'Aguardando aprovação',
  APPROVED: 'Aprovada', DONE: 'Concluída', CANCELLED: 'Cancelada',
}
const workOrderStatusColor: Record<string, string> = {
  OPEN: 'bg-slate-100 text-slate-600', IN_PROGRESS: 'bg-blue-50 text-blue-600',
  AWAITING_APPROVAL: 'bg-amber-50 text-amber-600', APPROVED: 'bg-indigo-50 text-indigo-600',
  DONE: 'bg-emerald-50 text-emerald-600', CANCELLED: 'bg-red-50 text-red-500',
}

type NewWorkOrderItemDraft = { kind: 'PART' | 'SERVICE'; description: string; stock_item_id?: number; quantity: number; unit_price: number }

function NewWorkOrderModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [customers, setCustomers] = useState<CustomerListItem[]>([])
  const [stockItems, setStockItems] = useState<StockItem[]>([])
  const [customerId, setCustomerId] = useState<number | ''>('')
  const [description, setDescription] = useState('')
  const [laborValue, setLaborValue] = useState(0)
  const [discountValue, setDiscountValue] = useState(0)
  const [nextRevisionDate, setNextRevisionDate] = useState('')
  const [items, setItems] = useState<NewWorkOrderItemDraft[]>([])
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    listCustomers().then(setCustomers).catch(() => {})
    listStock().then(setStockItems).catch(() => {})
  }, [])

  function addItem(kind: 'PART' | 'SERVICE') {
    setItems(prev => [...prev, { kind, description: '', quantity: 1, unit_price: 0 }])
  }
  function updateItem(idx: number, patch: Partial<NewWorkOrderItemDraft>) {
    setItems(prev => prev.map((it, i) => i === idx ? { ...it, ...patch } : it))
  }
  function removeItem(idx: number) {
    setItems(prev => prev.filter((_, i) => i !== idx))
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!customerId) { setError('Selecione um cliente.'); return }
    setBusy(true); setError('')
    try {
      await createWorkOrder({
        customer_id: Number(customerId),
        description,
        labor_value: laborValue,
        discount_value: discountValue,
        next_revision_date: nextRevisionDate || undefined,
        items: items.filter(it => it.description.trim()).map(it => ({
          kind: it.kind, description: it.description, stock_item_id: it.stock_item_id,
          quantity: it.quantity, unit_price: it.unit_price,
        })),
      })
      onCreated()
      onClose()
    } catch {
      setError('Não foi possível criar a ordem de serviço.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="fixed inset-0 z-20 grid place-items-center overflow-y-auto bg-slate-950/40 p-5" onClick={onClose}>
      <form onSubmit={handleSubmit} onClick={e => e.stopPropagation()}
        className="w-full max-w-lg rounded-3xl border border-slate-200 bg-white p-6 shadow-soft">
        <div className="mb-5 flex items-center justify-between">
          <h2 className="font-black">Nova ordem de serviço</h2>
          <button type="button" onClick={onClose} className="rounded-lg p-1 text-slate-400 hover:bg-slate-100"><X size={18}/></button>
        </div>

        <label className="mb-3 block text-sm">
          <span className="mb-1 block text-slate-600">Cliente *</span>
          <select value={customerId} onChange={e=>setCustomerId(e.target.value ? Number(e.target.value) : '')} required
            className="w-full rounded-xl border border-slate-200 px-3 py-2.5 outline-none focus:border-slate-400">
            <option value="">Selecione...</option>
            {customers.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
        </label>

        <label className="mb-3 block text-sm">
          <span className="mb-1 block text-slate-600">Descrição</span>
          <input value={description} onChange={e=>setDescription(e.target.value)}
            className="w-full rounded-xl border border-slate-200 px-3 py-2.5 outline-none focus:border-slate-400"/>
        </label>

        <div className="mb-3 grid grid-cols-3 gap-3">
          <label className="block text-sm">
            <span className="mb-1 block text-slate-600">Mão de obra (R$)</span>
            <input type="number" min={0} step="0.01" value={laborValue} onChange={e=>setLaborValue(Number(e.target.value))}
              className="w-full rounded-xl border border-slate-200 px-3 py-2.5 outline-none focus:border-slate-400"/>
          </label>
          <label className="block text-sm">
            <span className="mb-1 block text-slate-600">Desconto (R$)</span>
            <input type="number" min={0} step="0.01" value={discountValue} onChange={e=>setDiscountValue(Number(e.target.value))}
              className="w-full rounded-xl border border-slate-200 px-3 py-2.5 outline-none focus:border-slate-400"/>
          </label>
          <label className="block text-sm">
            <span className="mb-1 block text-slate-600">Próxima revisão</span>
            <input type="date" value={nextRevisionDate} onChange={e=>setNextRevisionDate(e.target.value)}
              className="w-full rounded-xl border border-slate-200 px-3 py-2.5 outline-none focus:border-slate-400"/>
          </label>
        </div>

        <div className="mb-4 rounded-2xl border border-slate-200 p-3">
          <div className="mb-2 flex items-center justify-between">
            <span className="text-sm font-bold text-slate-600">Itens</span>
            <div className="flex gap-2">
              <button type="button" onClick={()=>addItem('PART')} className="rounded-lg border border-slate-200 px-2.5 py-1 text-xs font-bold">+ Peça</button>
              <button type="button" onClick={()=>addItem('SERVICE')} className="rounded-lg border border-slate-200 px-2.5 py-1 text-xs font-bold">+ Serviço</button>
            </div>
          </div>
          {items.length === 0 && <p className="text-xs text-slate-400">Nenhum item adicionado ainda.</p>}
          <div className="space-y-2">
            {items.map((it, idx) => (
              <div key={idx} className="flex flex-wrap items-center gap-2 rounded-xl bg-slate-50 p-2">
                <span className="rounded-full bg-slate-200 px-2 py-0.5 text-[10px] font-bold uppercase">{it.kind === 'PART' ? 'Peça' : 'Serviço'}</span>
                {it.kind === 'PART' ? (
                  <select value={it.stock_item_id ?? ''} onChange={e => {
                      const stockId = e.target.value ? Number(e.target.value) : undefined
                      const stock = stockItems.find(s => s.id === stockId)
                      updateItem(idx, { stock_item_id: stockId, description: stock?.name ?? it.description, unit_price: stock?.sale_price ?? it.unit_price })
                    }}
                    className="min-w-[140px] flex-1 rounded-lg border border-slate-200 px-2 py-1.5 text-xs outline-none">
                    <option value="">Escolher item do estoque...</option>
                    {stockItems.map(s => <option key={s.id} value={s.id}>{s.sku} — {s.name}</option>)}
                  </select>
                ) : (
                  <input value={it.description} onChange={e=>updateItem(idx, { description: e.target.value })}
                    placeholder="Descrição do serviço"
                    className="min-w-[140px] flex-1 rounded-lg border border-slate-200 px-2 py-1.5 text-xs outline-none"/>
                )}
                <input type="number" min={1} value={it.quantity} onChange={e=>updateItem(idx, { quantity: Number(e.target.value) })}
                  className="w-16 rounded-lg border border-slate-200 px-2 py-1.5 text-xs outline-none" title="Quantidade"/>
                <input type="number" min={0} step="0.01" value={it.unit_price} onChange={e=>updateItem(idx, { unit_price: Number(e.target.value) })}
                  className="w-24 rounded-lg border border-slate-200 px-2 py-1.5 text-xs outline-none" title="Preço unitário"/>
                <button type="button" onClick={()=>removeItem(idx)} className="ml-auto rounded-lg p-1 text-slate-400 hover:bg-slate-200"><X size={14}/></button>
              </div>
            ))}
          </div>
        </div>

        {error && <div className="mb-4 rounded-xl bg-red-50 px-3 py-2 text-sm text-red-600">{error}</div>}
        <button disabled={busy} className="w-full rounded-xl bg-slate-950 px-4 py-2.5 text-sm font-bold text-white disabled:opacity-50">
          {busy ? 'Salvando...' : 'Criar ordem de serviço'}
        </button>
      </form>
    </div>
  )
}

function WorkOrdersPage() {
  const [items, setItems] = useState<WorkOrder[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [actionError, setActionError] = useState('')
  const [showNew, setShowNew] = useState(false)
  const [busyId, setBusyId] = useState<number | null>(null)

  function reload() {
    setLoading(true); setError('')
    listWorkOrders().then(setItems).catch(() => setError('Não foi possível carregar as ordens de serviço.')).finally(() => setLoading(false))
  }

  useEffect(() => { reload() }, [])

  async function handleClose(id: number) {
    setBusyId(id); setActionError('')
    try {
      await closeWorkOrder(id)
      reload()
    } catch {
      setActionError('Não foi possível concluir — confira se há estoque suficiente para as peças usadas.')
    } finally {
      setBusyId(null)
    }
  }

  async function handleCancel(id: number) {
    setBusyId(id); setActionError('')
    try {
      await cancelWorkOrder(id)
      reload()
    } catch {
      setActionError('Não foi possível cancelar esta ordem de serviço.')
    } finally {
      setBusyId(null)
    }
  }

  return (
    <section className="mx-auto max-w-7xl space-y-6 p-5 md:p-8">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <div className="text-xs font-semibold uppercase tracking-[.18em] text-slate-400">Operação</div>
          <h1 className="text-xl font-black">Ordens de serviço</h1>
        </div>
        <button onClick={()=>setShowNew(true)}
          className="flex items-center gap-2 rounded-xl bg-slate-950 px-4 py-2 text-sm font-bold text-white">
          <Plus size={16}/> Nova ordem de serviço
        </button>
      </div>

      {actionError && <div className="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-600">{actionError}</div>}

      <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-soft">
        {loading && <div className="p-6 text-sm text-slate-400">Carregando...</div>}
        {error && <div className="p-6 text-sm text-red-600">{error}</div>}
        {!loading && !error && items.length === 0 && (
          <div className="p-6 text-sm text-slate-400">Nenhuma ordem de serviço ainda.</div>
        )}
        {!loading && !error && items.length > 0 && (
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-left text-xs font-bold uppercase tracking-wider text-slate-400">
              <tr>
                <th className="px-5 py-3">#</th><th className="px-5 py-3">Cliente</th>
                <th className="px-5 py-3">Status</th><th className="px-5 py-3">Total</th>
                <th className="px-5 py-3">Próx. revisão</th><th className="px-5 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {items.map(wo => (
                <tr key={wo.id} className="border-t border-slate-100">
                  <td className="px-5 py-3 font-mono text-xs text-slate-500">#{wo.id}</td>
                  <td className="px-5 py-3 font-semibold">{wo.customer_name || '—'}</td>
                  <td className="px-5 py-3">
                    <span className={`rounded-full px-2.5 py-1 text-xs font-bold ${workOrderStatusColor[wo.status]}`}>{workOrderStatusLabel[wo.status]}</span>
                  </td>
                  <td className="px-5 py-3 text-slate-500">R$ {wo.total_value.toFixed(2)}</td>
                  <td className="px-5 py-3 text-slate-500">{wo.next_revision_date ?? '—'}</td>
                  <td className="px-5 py-3 text-right">
                    {wo.status !== 'DONE' && wo.status !== 'CANCELLED' && (
                      <div className="flex justify-end gap-3">
                        <button disabled={busyId===wo.id} onClick={()=>handleClose(wo.id)} className="text-xs font-bold text-emerald-600 hover:underline disabled:opacity-50">
                          Concluir
                        </button>
                        <button disabled={busyId===wo.id} onClick={()=>handleCancel(wo.id)} className="text-xs font-bold text-red-500 hover:underline disabled:opacity-50">
                          Cancelar
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {showNew && <NewWorkOrderModal onClose={()=>setShowNew(false)} onCreated={reload} />}
    </section>
  )
}

function MonthlyBarChart({ series }: { series: DashboardReport['monthly_series'] }) {
  if (series.length === 0) {
    return <p className="text-sm text-slate-400">Sem ordens de serviço concluídas ainda para comparar meses.</p>
  }
  const maxValue = Math.max(1, ...series.flatMap(p => [p.revenue, p.profit]))
  const monthLabel = (m: string) => {
    const [y, mo] = m.split('-')
    const names = ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez']
    return `${names[Number(mo) - 1]}/${y.slice(2)}`
  }
  return (
    <div>
      <div className="flex h-48 items-end gap-4">
        {series.map(p => (
          <div key={p.month} className="flex flex-1 flex-col items-center gap-1">
            <div className="flex h-40 w-full items-end justify-center gap-1">
              <div className="w-3 rounded-t-md bg-slate-800" style={{ height: `${(p.revenue / maxValue) * 100}%` }} title={`Receita: R$ ${p.revenue.toFixed(2)}`}/>
              <div className="w-3 rounded-t-md bg-emerald-400" style={{ height: `${(p.profit / maxValue) * 100}%` }} title={`Lucro: R$ ${p.profit.toFixed(2)}`}/>
            </div>
            <span className="text-[11px] font-semibold text-slate-400">{monthLabel(p.month)}</span>
          </div>
        ))}
      </div>
      <div className="mt-3 flex gap-4 text-xs text-slate-500">
        <span className="flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-full bg-slate-800"/>Receita</span>
        <span className="flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-full bg-emerald-400"/>Lucro</span>
      </div>
    </div>
  )
}

function ReportsPage() {
  const [report, setReport] = useState<DashboardReport | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    getDashboardReport().then(setReport).catch(() => setError('Não foi possível carregar os relatórios.')).finally(() => setLoading(false))
  }, [])

  if (loading) return <section className="p-8 text-sm text-slate-400">Carregando relatórios...</section>
  if (error || !report) return <section className="p-8 text-sm text-red-600">{error || 'Sem dados.'}</section>

  const revenueDelta = report.revenue_this_month - report.revenue_last_month
  const profitDelta = report.profit_this_month - report.profit_last_month

  return (
    <section className="mx-auto max-w-7xl space-y-6 p-5 md:p-8">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-soft">
          <div className="text-sm text-slate-500">Valor em estoque</div>
          <div className="mt-2 text-3xl font-black">R$ {report.stock_value.toFixed(2)}</div>
          <div className="mt-2 flex items-center gap-1 text-xs font-semibold text-amber-500"><AlertTriangle size={13}/> {report.stock_critical_items} itens críticos</div>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-soft">
          <div className="text-sm text-slate-500">OS em aberto</div>
          <div className="mt-2 text-3xl font-black">{report.open_work_orders}</div>
          <div className="mt-2 text-xs font-semibold text-slate-400">não concluídas nem canceladas</div>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-soft">
          <div className="text-sm text-slate-500">Clientes</div>
          <div className="mt-2 text-3xl font-black">{report.customers_total}</div>
          <div className="mt-2 text-xs font-semibold text-slate-400">+{report.customers_new_this_month} este mês</div>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-soft">
          <div className="text-sm text-slate-500">Lucro do mês</div>
          <div className="mt-2 text-3xl font-black">R$ {report.profit_this_month.toFixed(2)}</div>
          <div className={`mt-2 flex items-center gap-1 text-xs font-semibold ${profitDelta >= 0 ? 'text-emerald-500' : 'text-red-500'}`}>
            {profitDelta >= 0 ? <TrendingUp size={13}/> : <TrendingDown size={13}/>} R$ {Math.abs(profitDelta).toFixed(2)} vs. mês anterior
          </div>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-soft">
          <div className="text-sm text-slate-500">A receber em aberto</div>
          <div className="mt-2 text-2xl font-black text-emerald-600">R$ {report.receivables_pending.toFixed(2)}</div>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-soft">
          <div className="text-sm text-slate-500">A pagar em aberto</div>
          <div className="mt-2 text-2xl font-black text-red-500">R$ {report.payables_pending.toFixed(2)}</div>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-soft">
          <div className="text-sm text-slate-500">Saldo do caixa aberto</div>
          <div className="mt-2 text-2xl font-black">{report.cash_balance != null ? `R$ ${report.cash_balance.toFixed(2)}` : '—'}</div>
          {report.cash_balance == null && <div className="mt-1 text-xs text-slate-400">Nenhum caixa aberto no momento</div>}
        </div>
      </div>

      <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-soft">
        <div className="mb-1 flex items-center justify-between">
          <h2 className="font-black">Receita e lucro por mês</h2>
          <span className={`flex items-center gap-1 text-xs font-bold ${revenueDelta >= 0 ? 'text-emerald-500' : 'text-red-500'}`}>
            {revenueDelta >= 0 ? <TrendingUp size={14}/> : <TrendingDown size={14}/>} R$ {Math.abs(revenueDelta).toFixed(2)} de receita vs. mês anterior
          </span>
        </div>
        <p className="mb-6 text-sm text-slate-500">Baseado nas ordens de serviço concluídas em cada mês.</p>
        <MonthlyBarChart series={report.monthly_series} />
      </div>
    </section>
  )
}

const financeStatusLabel: Record<string, string> = { PENDING: 'Em aberto', PAID: 'Quitado', OVERDUE: 'Vencido', CANCELLED: 'Cancelado' }
const financeStatusColor: Record<string, string> = {
  PENDING: 'bg-slate-100 text-slate-600', PAID: 'bg-emerald-50 text-emerald-600',
  OVERDUE: 'bg-red-50 text-red-500', CANCELLED: 'bg-slate-100 text-slate-400',
}

function NewFinanceEntryModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [type, setType] = useState<'PAYABLE' | 'RECEIVABLE'>('PAYABLE')
  const [category, setCategory] = useState('')
  const [description, setDescription] = useState('')
  const [amount, setAmount] = useState(0)
  const [dueDate, setDueDate] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!dueDate) { setError('Informe o vencimento.'); return }
    setBusy(true); setError('')
    try {
      await createFinanceEntry({ type, category, description, amount, due_date: dueDate })
      onCreated()
      onClose()
    } catch {
      setError('Não foi possível salvar o lançamento.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="fixed inset-0 z-20 grid place-items-center bg-slate-950/40 p-5" onClick={onClose}>
      <form onSubmit={handleSubmit} onClick={e => e.stopPropagation()}
        className="w-full max-w-md rounded-3xl border border-slate-200 bg-white p-6 shadow-soft">
        <div className="mb-5 flex items-center justify-between">
          <h2 className="font-black">Novo lançamento</h2>
          <button type="button" onClick={onClose} className="rounded-lg p-1 text-slate-400 hover:bg-slate-100"><X size={18}/></button>
        </div>

        <div className="mb-3 flex gap-2">
          <button type="button" onClick={()=>setType('PAYABLE')}
            className={`flex-1 rounded-xl border px-3 py-2 text-sm font-bold ${type==='PAYABLE' ? 'border-slate-950 bg-slate-950 text-white' : 'border-slate-200 text-slate-600'}`}>A pagar</button>
          <button type="button" onClick={()=>setType('RECEIVABLE')}
            className={`flex-1 rounded-xl border px-3 py-2 text-sm font-bold ${type==='RECEIVABLE' ? 'border-slate-950 bg-slate-950 text-white' : 'border-slate-200 text-slate-600'}`}>A receber</button>
        </div>

        <label className="mb-3 block text-sm">
          <span className="mb-1 block text-slate-600">Categoria</span>
          <input value={category} onChange={e=>setCategory(e.target.value)} placeholder="Ex.: Fornecedor, aluguel, venda avulsa..."
            className="w-full rounded-xl border border-slate-200 px-3 py-2.5 outline-none focus:border-slate-400"/>
        </label>
        <label className="mb-3 block text-sm">
          <span className="mb-1 block text-slate-600">Descrição</span>
          <input value={description} onChange={e=>setDescription(e.target.value)}
            className="w-full rounded-xl border border-slate-200 px-3 py-2.5 outline-none focus:border-slate-400"/>
        </label>
        <div className="mb-4 grid grid-cols-2 gap-3">
          <label className="block text-sm">
            <span className="mb-1 block text-slate-600">Valor (R$) *</span>
            <input type="number" min={0.01} step="0.01" value={amount} onChange={e=>setAmount(Number(e.target.value))} required
              className="w-full rounded-xl border border-slate-200 px-3 py-2.5 outline-none focus:border-slate-400"/>
          </label>
          <label className="block text-sm">
            <span className="mb-1 block text-slate-600">Vencimento *</span>
            <input type="date" value={dueDate} onChange={e=>setDueDate(e.target.value)} required
              className="w-full rounded-xl border border-slate-200 px-3 py-2.5 outline-none focus:border-slate-400"/>
          </label>
        </div>
        {error && <div className="mb-4 rounded-xl bg-red-50 px-3 py-2 text-sm text-red-600">{error}</div>}
        <button disabled={busy} className="w-full rounded-xl bg-slate-950 px-4 py-2.5 text-sm font-bold text-white disabled:opacity-50">
          {busy ? 'Salvando...' : 'Salvar lançamento'}
        </button>
      </form>
    </div>
  )
}

function FinanceEntriesPanel() {
  const [entries, setEntries] = useState<FinanceEntry[]>([])
  const [filterType, setFilterType] = useState<'' | 'PAYABLE' | 'RECEIVABLE'>('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [actionError, setActionError] = useState('')
  const [showNew, setShowNew] = useState(false)
  const [busyId, setBusyId] = useState<number | null>(null)

  function reload() {
    setLoading(true); setError('')
    listFinanceEntries({ type: filterType || undefined }).then(setEntries)
      .catch(() => setError('Não foi possível carregar os lançamentos.')).finally(() => setLoading(false))
  }

  useEffect(() => { reload() }, [filterType])

  async function handlePay(id: number) {
    setBusyId(id); setActionError('')
    try { await payFinanceEntry(id); reload() }
    catch { setActionError('Não foi possível registrar o pagamento/recebimento.') }
    finally { setBusyId(null) }
  }

  async function handleCancel(id: number) {
    setBusyId(id); setActionError('')
    try { await cancelFinanceEntry(id); reload() }
    catch { setActionError('Não foi possível cancelar este lançamento.') }
    finally { setBusyId(null) }
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div className="flex gap-2">
          {(['', 'PAYABLE', 'RECEIVABLE'] as const).map(t => (
            <button key={t} onClick={()=>setFilterType(t)}
              className={`rounded-xl border px-3 py-2 text-sm font-bold ${filterType===t ? 'border-slate-950 bg-slate-950 text-white' : 'border-slate-200 text-slate-600'}`}>
              {t === '' ? 'Todos' : t === 'PAYABLE' ? 'A pagar' : 'A receber'}
            </button>
          ))}
        </div>
        <button onClick={()=>setShowNew(true)} className="flex items-center gap-2 rounded-xl bg-slate-950 px-4 py-2 text-sm font-bold text-white">
          <Plus size={16}/> Novo lançamento
        </button>
      </div>

      {actionError && <div className="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-600">{actionError}</div>}

      <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-soft">
        {loading && <div className="p-6 text-sm text-slate-400">Carregando...</div>}
        {error && <div className="p-6 text-sm text-red-600">{error}</div>}
        {!loading && !error && entries.length === 0 && <div className="p-6 text-sm text-slate-400">Nenhum lançamento encontrado.</div>}
        {!loading && !error && entries.length > 0 && (
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-left text-xs font-bold uppercase tracking-wider text-slate-400">
              <tr>
                <th className="px-5 py-3">Tipo</th><th className="px-5 py-3">Descrição</th>
                <th className="px-5 py-3">Vencimento</th><th className="px-5 py-3">Valor</th>
                <th className="px-5 py-3">Saldo</th><th className="px-5 py-3">Status</th><th className="px-5 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {entries.map(e => (
                <tr key={e.id} className="border-t border-slate-100">
                  <td className="px-5 py-3 text-xs font-bold text-slate-500">{e.type === 'PAYABLE' ? 'A pagar' : 'A receber'}</td>
                  <td className="px-5 py-3 font-semibold">{e.description || e.category || '—'}{e.customer_name ? ` · ${e.customer_name}` : ''}</td>
                  <td className="px-5 py-3 text-slate-500">{e.due_date}</td>
                  <td className="px-5 py-3 text-slate-500">R$ {e.amount.toFixed(2)}</td>
                  <td className="px-5 py-3 text-slate-500">R$ {e.remaining_amount.toFixed(2)}</td>
                  <td className="px-5 py-3">
                    <span className={`rounded-full px-2.5 py-1 text-xs font-bold ${financeStatusColor[e.status]}`}>{financeStatusLabel[e.status]}</span>
                  </td>
                  <td className="px-5 py-3 text-right">
                    {(e.status === 'PENDING' || e.status === 'OVERDUE') && (
                      <div className="flex justify-end gap-3">
                        <button disabled={busyId===e.id} onClick={()=>handlePay(e.id)} className="text-xs font-bold text-emerald-600 hover:underline disabled:opacity-50">Quitar</button>
                        <button disabled={busyId===e.id} onClick={()=>handleCancel(e.id)} className="text-xs font-bold text-red-500 hover:underline disabled:opacity-50">Cancelar</button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {showNew && <NewFinanceEntryModal onClose={()=>setShowNew(false)} onCreated={reload} />}
    </div>
  )
}

function CashPanel() {
  const [session, setSession] = useState<CashSession | null>(null)
  const [movements, setMovements] = useState<CashMovement[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [openingAmount, setOpeningAmount] = useState(0)
  const [closingCounted, setClosingCounted] = useState(0)
  const [movementType, setMovementType] = useState<'IN' | 'OUT'>('OUT')
  const [movementAmount, setMovementAmount] = useState(0)
  const [movementDescription, setMovementDescription] = useState('')
  const [busy, setBusy] = useState(false)
  const [actionError, setActionError] = useState('')

  function reload() {
    setLoading(true); setError('')
    getCurrentCashSession()
      .then(s => {
        setSession(s)
        if (s) return listCashMovements(s.id).then(setMovements)
        setMovements([])
      })
      .catch(() => setError('Não foi possível carregar o caixa.'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { reload() }, [])

  async function handleOpen(e: React.FormEvent) {
    e.preventDefault()
    setBusy(true); setActionError('')
    try { await openCashSession(openingAmount); reload() }
    catch { setActionError('Não foi possível abrir o caixa.') }
    finally { setBusy(false) }
  }

  async function handleClose(e: React.FormEvent) {
    e.preventDefault()
    if (!session) return
    setBusy(true); setActionError('')
    try { await closeCashSession(session.id, closingCounted); reload() }
    catch { setActionError('Não foi possível fechar o caixa.') }
    finally { setBusy(false) }
  }

  async function handleMovement(e: React.FormEvent) {
    e.preventDefault()
    if (!session) return
    setBusy(true); setActionError('')
    try {
      await addCashMovement(session.id, { type: movementType, amount: movementAmount, description: movementDescription })
      setMovementAmount(0); setMovementDescription('')
      reload()
    } catch {
      setActionError('Não foi possível lançar o movimento (saldo insuficiente para saída?).')
    } finally {
      setBusy(false)
    }
  }

  if (loading) return <div className="p-6 text-sm text-slate-400">Carregando caixa...</div>
  if (error) return <div className="p-6 text-sm text-red-600">{error}</div>

  if (!session) {
    return (
      <form onSubmit={handleOpen} className="max-w-sm space-y-3 rounded-3xl border border-slate-200 bg-white p-6 shadow-soft">
        <div className="flex items-center gap-2 text-slate-500"><Lock size={18}/><span className="font-black text-slate-950">Caixa fechado</span></div>
        <label className="block text-sm">
          <span className="mb-1 block text-slate-600">Valor de abertura (R$)</span>
          <input type="number" min={0} step="0.01" value={openingAmount} onChange={e=>setOpeningAmount(Number(e.target.value))}
            className="w-full rounded-xl border border-slate-200 px-3 py-2.5 outline-none focus:border-slate-400"/>
        </label>
        {actionError && <div className="rounded-xl bg-red-50 px-3 py-2 text-sm text-red-600">{actionError}</div>}
        <button disabled={busy} className="w-full rounded-xl bg-slate-950 px-4 py-2.5 text-sm font-bold text-white disabled:opacity-50">
          {busy ? 'Abrindo...' : 'Abrir caixa'}
        </button>
      </form>
    )
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[1fr_1.2fr]">
      <div className="space-y-4">
        <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-soft">
          <div className="mb-4 flex items-center gap-2 text-emerald-600"><Unlock size={18}/><span className="font-black text-slate-950">Caixa aberto</span></div>
          <div className="text-sm text-slate-500">Saldo atual</div>
          <div className="text-3xl font-black">R$ {session.current_balance.toFixed(2)}</div>
          <div className="mt-2 text-xs text-slate-400">Abertura: R$ {session.opening_amount.toFixed(2)}</div>
        </div>

        <form onSubmit={handleMovement} className="space-y-3 rounded-3xl border border-slate-200 bg-white p-6 shadow-soft">
          <div className="font-black">Lançar movimento manual</div>
          <div className="flex gap-2">
            <button type="button" onClick={()=>setMovementType('IN')}
              className={`flex-1 rounded-xl border px-3 py-2 text-sm font-bold ${movementType==='IN' ? 'border-slate-950 bg-slate-950 text-white' : 'border-slate-200 text-slate-600'}`}>Reforço</button>
            <button type="button" onClick={()=>setMovementType('OUT')}
              className={`flex-1 rounded-xl border px-3 py-2 text-sm font-bold ${movementType==='OUT' ? 'border-slate-950 bg-slate-950 text-white' : 'border-slate-200 text-slate-600'}`}>Sangria</button>
          </div>
          <input type="number" min={0.01} step="0.01" value={movementAmount} onChange={e=>setMovementAmount(Number(e.target.value))}
            placeholder="Valor (R$)" className="w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm outline-none focus:border-slate-400"/>
          <input value={movementDescription} onChange={e=>setMovementDescription(e.target.value)}
            placeholder="Motivo" className="w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm outline-none focus:border-slate-400"/>
          <button disabled={busy} className="w-full rounded-xl bg-slate-950 px-4 py-2.5 text-sm font-bold text-white disabled:opacity-50">
            {busy ? 'Salvando...' : 'Confirmar movimento'}
          </button>
        </form>

        <form onSubmit={handleClose} className="space-y-3 rounded-3xl border border-slate-200 bg-white p-6 shadow-soft">
          <div className="font-black">Fechar caixa</div>
          <label className="block text-sm">
            <span className="mb-1 block text-slate-600">Valor contado na gaveta (R$)</span>
            <input type="number" min={0} step="0.01" value={closingCounted} onChange={e=>setClosingCounted(Number(e.target.value))}
              className="w-full rounded-xl border border-slate-200 px-3 py-2.5 outline-none focus:border-slate-400"/>
          </label>
          {actionError && <div className="rounded-xl bg-red-50 px-3 py-2 text-sm text-red-600">{actionError}</div>}
          <button disabled={busy} className="w-full rounded-xl border border-slate-300 px-4 py-2.5 text-sm font-bold text-slate-700 disabled:opacity-50">
            {busy ? 'Fechando...' : 'Fechar caixa'}
          </button>
        </form>
      </div>

      <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-soft">
        <div className="border-b border-slate-100 p-5 font-black">Movimentações da sessão</div>
        {movements.length === 0 ? (
          <div className="p-6 text-sm text-slate-400">Nenhuma movimentação ainda.</div>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-left text-xs font-bold uppercase tracking-wider text-slate-400">
              <tr><th className="px-5 py-3">Tipo</th><th className="px-5 py-3">Descrição</th><th className="px-5 py-3">Valor</th></tr>
            </thead>
            <tbody>
              {movements.map(m => (
                <tr key={m.id} className="border-t border-slate-100">
                  <td className="px-5 py-3"><span className={`rounded-full px-2.5 py-1 text-xs font-bold ${m.type==='IN' ? 'bg-emerald-50 text-emerald-600' : 'bg-red-50 text-red-500'}`}>{m.type==='IN' ? 'Entrada' : 'Saída'}</span></td>
                  <td className="px-5 py-3 text-slate-600">{m.description || '—'}</td>
                  <td className="px-5 py-3 font-semibold">R$ {m.amount.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}

function FinancePage() {
  const [tab, setTab] = useState<'entries' | 'cash'>('entries')
  return (
    <section className="mx-auto max-w-7xl space-y-6 p-5 md:p-8">
      <div className="flex items-center gap-2">
        <button onClick={()=>setTab('entries')}
          className={`flex items-center gap-2 rounded-xl border px-4 py-2 text-sm font-bold ${tab==='entries' ? 'border-slate-950 bg-slate-950 text-white' : 'border-slate-200 text-slate-600'}`}>
          <DollarSign size={16}/> Contas a pagar/receber
        </button>
        <button onClick={()=>setTab('cash')}
          className={`flex items-center gap-2 rounded-xl border px-4 py-2 text-sm font-bold ${tab==='cash' ? 'border-slate-950 bg-slate-950 text-white' : 'border-slate-200 text-slate-600'}`}>
          <Wallet size={16}/> Caixa
        </button>
      </div>
      {tab === 'entries' ? <FinanceEntriesPanel /> : <CashPanel />}
    </section>
  )
}

const purchaseStatusLabel: Record<string, string> = { DRAFT: 'Rascunho', ORDERED: 'Pedido feito', RECEIVED: 'Recebido', CANCELLED: 'Cancelado' }
const purchaseStatusColor: Record<string, string> = {
  DRAFT: 'bg-slate-100 text-slate-600', ORDERED: 'bg-blue-50 text-blue-600',
  RECEIVED: 'bg-emerald-50 text-emerald-600', CANCELLED: 'bg-red-50 text-red-500',
}

function NewSupplierModal({ onClose, onCreated }: { onClose: () => void; onCreated: (s: Supplier) => void }) {
  const [name, setName] = useState('')
  const [document, setDocument] = useState('')
  const [phone, setPhone] = useState('')
  const [email, setEmail] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setBusy(true); setError('')
    try {
      const s = await createSupplier({ name, document, phone, email })
      onCreated(s)
      onClose()
    } catch {
      setError('Não foi possível salvar o fornecedor.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="fixed inset-0 z-30 grid place-items-center bg-slate-950/40 p-5" onClick={onClose}>
      <form onSubmit={handleSubmit} onClick={e => e.stopPropagation()}
        className="w-full max-w-sm rounded-3xl border border-slate-200 bg-white p-6 shadow-soft">
        <div className="mb-5 flex items-center justify-between">
          <h2 className="font-black">Novo fornecedor</h2>
          <button type="button" onClick={onClose} className="rounded-lg p-1 text-slate-400 hover:bg-slate-100"><X size={18}/></button>
        </div>
        <label className="mb-3 block text-sm">
          <span className="mb-1 block text-slate-600">Nome *</span>
          <input value={name} onChange={e=>setName(e.target.value)} required
            className="w-full rounded-xl border border-slate-200 px-3 py-2.5 outline-none focus:border-slate-400"/>
        </label>
        <label className="mb-3 block text-sm">
          <span className="mb-1 block text-slate-600">CNPJ/CPF</span>
          <input value={document} onChange={e=>setDocument(e.target.value)}
            className="w-full rounded-xl border border-slate-200 px-3 py-2.5 outline-none focus:border-slate-400"/>
        </label>
        <div className="mb-4 grid grid-cols-2 gap-3">
          <label className="block text-sm">
            <span className="mb-1 block text-slate-600">Telefone</span>
            <input value={phone} onChange={e=>setPhone(e.target.value)}
              className="w-full rounded-xl border border-slate-200 px-3 py-2.5 outline-none focus:border-slate-400"/>
          </label>
          <label className="block text-sm">
            <span className="mb-1 block text-slate-600">E-mail</span>
            <input value={email} onChange={e=>setEmail(e.target.value)}
              className="w-full rounded-xl border border-slate-200 px-3 py-2.5 outline-none focus:border-slate-400"/>
          </label>
        </div>
        {error && <div className="mb-4 rounded-xl bg-red-50 px-3 py-2 text-sm text-red-600">{error}</div>}
        <button disabled={busy} className="w-full rounded-xl bg-slate-950 px-4 py-2.5 text-sm font-bold text-white disabled:opacity-50">
          {busy ? 'Salvando...' : 'Salvar fornecedor'}
        </button>
      </form>
    </div>
  )
}

type NewPurchaseItemDraft = { description: string; stock_item_id?: number; quantity: number; unit_cost: number }

function NewPurchaseOrderModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [suppliers, setSuppliers] = useState<Supplier[]>([])
  const [stockItems, setStockItems] = useState<StockItem[]>([])
  const [supplierId, setSupplierId] = useState<number | ''>('')
  const [notes, setNotes] = useState('')
  const [paymentDueDate, setPaymentDueDate] = useState('')
  const [items, setItems] = useState<NewPurchaseItemDraft[]>([])
  const [showNewSupplier, setShowNewSupplier] = useState(false)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  function reloadSuppliers() {
    listSuppliers().then(setSuppliers).catch(() => {})
  }

  useEffect(() => {
    reloadSuppliers()
    listStock().then(setStockItems).catch(() => {})
  }, [])

  function addItem() {
    setItems(prev => [...prev, { description: '', quantity: 1, unit_cost: 0 }])
  }
  function updateItem(idx: number, patch: Partial<NewPurchaseItemDraft>) {
    setItems(prev => prev.map((it, i) => i === idx ? { ...it, ...patch } : it))
  }
  function removeItem(idx: number) {
    setItems(prev => prev.filter((_, i) => i !== idx))
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!supplierId) { setError('Selecione um fornecedor.'); return }
    setBusy(true); setError('')
    try {
      await createPurchaseOrder({
        supplier_id: Number(supplierId),
        notes,
        payment_due_date: paymentDueDate || undefined,
        items: items.filter(it => it.description.trim()).map(it => ({
          description: it.description, stock_item_id: it.stock_item_id, quantity: it.quantity, unit_cost: it.unit_cost,
        })),
      })
      onCreated()
      onClose()
    } catch {
      setError('Não foi possível criar o pedido de compra.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="fixed inset-0 z-20 grid place-items-center overflow-y-auto bg-slate-950/40 p-5" onClick={onClose}>
      <form onSubmit={handleSubmit} onClick={e => e.stopPropagation()}
        className="w-full max-w-lg rounded-3xl border border-slate-200 bg-white p-6 shadow-soft">
        <div className="mb-5 flex items-center justify-between">
          <h2 className="font-black">Novo pedido de compra</h2>
          <button type="button" onClick={onClose} className="rounded-lg p-1 text-slate-400 hover:bg-slate-100"><X size={18}/></button>
        </div>

        <label className="mb-1 block text-sm">
          <span className="mb-1 block text-slate-600">Fornecedor *</span>
          <div className="flex gap-2">
            <select value={supplierId} onChange={e=>setSupplierId(e.target.value ? Number(e.target.value) : '')} required
              className="w-full rounded-xl border border-slate-200 px-3 py-2.5 outline-none focus:border-slate-400">
              <option value="">Selecione...</option>
              {suppliers.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
            </select>
            <button type="button" onClick={()=>setShowNewSupplier(true)}
              className="whitespace-nowrap rounded-xl border border-slate-200 px-3 py-2 text-xs font-bold text-slate-600">+ Novo</button>
          </div>
        </label>

        <div className="mb-3 mt-3 grid grid-cols-2 gap-3">
          <label className="block text-sm">
            <span className="mb-1 block text-slate-600">Observações</span>
            <input value={notes} onChange={e=>setNotes(e.target.value)}
              className="w-full rounded-xl border border-slate-200 px-3 py-2.5 outline-none focus:border-slate-400"/>
          </label>
          <label className="block text-sm">
            <span className="mb-1 block text-slate-600">Vencimento do pagamento</span>
            <input type="date" value={paymentDueDate} onChange={e=>setPaymentDueDate(e.target.value)}
              className="w-full rounded-xl border border-slate-200 px-3 py-2.5 outline-none focus:border-slate-400"/>
          </label>
        </div>

        <div className="mb-4 rounded-2xl border border-slate-200 p-3">
          <div className="mb-2 flex items-center justify-between">
            <span className="text-sm font-bold text-slate-600">Itens</span>
            <button type="button" onClick={addItem} className="rounded-lg border border-slate-200 px-2.5 py-1 text-xs font-bold">+ Item</button>
          </div>
          {items.length === 0 && <p className="text-xs text-slate-400">Nenhum item adicionado ainda.</p>}
          <div className="space-y-2">
            {items.map((it, idx) => (
              <div key={idx} className="flex flex-wrap items-center gap-2 rounded-xl bg-slate-50 p-2">
                <select value={it.stock_item_id ?? ''} onChange={e => {
                    const stockId = e.target.value ? Number(e.target.value) : undefined
                    const stock = stockItems.find(s => s.id === stockId)
                    updateItem(idx, { stock_item_id: stockId, description: stock?.name ?? it.description, unit_cost: stock?.cost_price ?? it.unit_cost })
                  }}
                  className="min-w-[140px] flex-1 rounded-lg border border-slate-200 px-2 py-1.5 text-xs outline-none">
                  <option value="">Item avulso (sem vincular ao estoque)...</option>
                  {stockItems.map(s => <option key={s.id} value={s.id}>{s.sku} — {s.name}</option>)}
                </select>
                {!it.stock_item_id && (
                  <input value={it.description} onChange={e=>updateItem(idx, { description: e.target.value })}
                    placeholder="Descrição do item"
                    className="min-w-[140px] flex-1 rounded-lg border border-slate-200 px-2 py-1.5 text-xs outline-none"/>
                )}
                <input type="number" min={1} value={it.quantity} onChange={e=>updateItem(idx, { quantity: Number(e.target.value) })}
                  className="w-16 rounded-lg border border-slate-200 px-2 py-1.5 text-xs outline-none" title="Quantidade"/>
                <input type="number" min={0} step="0.01" value={it.unit_cost} onChange={e=>updateItem(idx, { unit_cost: Number(e.target.value) })}
                  className="w-24 rounded-lg border border-slate-200 px-2 py-1.5 text-xs outline-none" title="Custo unitário"/>
                <button type="button" onClick={()=>removeItem(idx)} className="ml-auto rounded-lg p-1 text-slate-400 hover:bg-slate-200"><X size={14}/></button>
              </div>
            ))}
          </div>
        </div>

        {error && <div className="mb-4 rounded-xl bg-red-50 px-3 py-2 text-sm text-red-600">{error}</div>}
        <button disabled={busy} className="w-full rounded-xl bg-slate-950 px-4 py-2.5 text-sm font-bold text-white disabled:opacity-50">
          {busy ? 'Salvando...' : 'Criar pedido de compra'}
        </button>
      </form>

      {showNewSupplier && (
        <NewSupplierModal
          onClose={()=>setShowNewSupplier(false)}
          onCreated={(s) => { reloadSuppliers(); setSupplierId(s.id) }}
        />
      )}
    </div>
  )
}

function PurchasesPage() {
  const [orders, setOrders] = useState<PurchaseOrder[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [actionError, setActionError] = useState('')
  const [showNew, setShowNew] = useState(false)
  const [busyId, setBusyId] = useState<number | null>(null)

  function reload() {
    setLoading(true); setError('')
    listPurchaseOrders().then(setOrders).catch(() => setError('Não foi possível carregar os pedidos de compra.')).finally(() => setLoading(false))
  }

  useEffect(() => { reload() }, [])

  async function handleReceive(id: number) {
    setBusyId(id); setActionError('')
    try { await receivePurchaseOrder(id); reload() }
    catch { setActionError('Não foi possível receber este pedido (confira se há itens cadastrados).') }
    finally { setBusyId(null) }
  }

  async function handleCancel(id: number) {
    setBusyId(id); setActionError('')
    try { await cancelPurchaseOrder(id); reload() }
    catch { setActionError('Não foi possível cancelar este pedido.') }
    finally { setBusyId(null) }
  }

  return (
    <section className="mx-auto max-w-7xl space-y-6 p-5 md:p-8">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <div className="text-xs font-semibold uppercase tracking-[.18em] text-slate-400">Suprimentos</div>
          <h1 className="text-xl font-black">Pedidos de compra</h1>
        </div>
        <button onClick={()=>setShowNew(true)} className="flex items-center gap-2 rounded-xl bg-slate-950 px-4 py-2 text-sm font-bold text-white">
          <Plus size={16}/> Novo pedido de compra
        </button>
      </div>

      {actionError && <div className="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-600">{actionError}</div>}

      <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-soft">
        {loading && <div className="p-6 text-sm text-slate-400">Carregando...</div>}
        {error && <div className="p-6 text-sm text-red-600">{error}</div>}
        {!loading && !error && orders.length === 0 && <div className="p-6 text-sm text-slate-400">Nenhum pedido de compra ainda.</div>}
        {!loading && !error && orders.length > 0 && (
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-left text-xs font-bold uppercase tracking-wider text-slate-400">
              <tr>
                <th className="px-5 py-3">#</th><th className="px-5 py-3">Fornecedor</th>
                <th className="px-5 py-3">Status</th><th className="px-5 py-3">Total</th>
                <th className="px-5 py-3">Venc. pagamento</th><th className="px-5 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {orders.map(po => (
                <tr key={po.id} className="border-t border-slate-100">
                  <td className="px-5 py-3 font-mono text-xs text-slate-500">#{po.id}</td>
                  <td className="px-5 py-3 flex items-center gap-2 font-semibold"><Truck size={14} className="text-slate-400"/>{po.supplier_name || '—'}</td>
                  <td className="px-5 py-3">
                    <span className={`rounded-full px-2.5 py-1 text-xs font-bold ${purchaseStatusColor[po.status]}`}>{purchaseStatusLabel[po.status]}</span>
                  </td>
                  <td className="px-5 py-3 text-slate-500">R$ {po.total_value.toFixed(2)}</td>
                  <td className="px-5 py-3 text-slate-500">{po.payment_due_date ?? '—'}</td>
                  <td className="px-5 py-3 text-right">
                    {po.status === 'ORDERED' && (
                      <div className="flex justify-end gap-3">
                        <button disabled={busyId===po.id} onClick={()=>handleReceive(po.id)} className="text-xs font-bold text-emerald-600 hover:underline disabled:opacity-50">Receber</button>
                        <button disabled={busyId===po.id} onClick={()=>handleCancel(po.id)} className="text-xs font-bold text-red-500 hover:underline disabled:opacity-50">Cancelar</button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {showNew && <NewPurchaseOrderModal onClose={()=>setShowNew(false)} onCreated={reload} />}
    </section>
  )
}

const actionLabel: Record<string, string> = {
  'auth.login': 'Login', 'auth.logout': 'Logout',
  'work_order.close': 'OS concluída', 'work_order.cancel': 'OS cancelada',
  'finance_entry.pay': 'Lançamento quitado', 'finance_entry.cancel': 'Lançamento cancelado',
  'cash_session.open': 'Caixa aberto', 'cash_session.close': 'Caixa fechado',
  'stock.adjust': 'Ajuste de estoque',
  'purchase_order.receive': 'Pedido de compra recebido', 'purchase_order.cancel': 'Pedido de compra cancelado',
}

function AuditPage() {
  const [logs, setLogs] = useState<AuditLog[]>([])
  const [actionFilter, setActionFilter] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  function reload() {
    setLoading(true); setError('')
    listAuditLogs({ action: actionFilter || undefined })
      .then(setLogs)
      .catch(() => setError('Não foi possível carregar a trilha de auditoria.'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { reload() }, [actionFilter])

  const knownActions = Object.keys(actionLabel)

  return (
    <section className="mx-auto max-w-7xl space-y-6 p-5 md:p-8">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <p className="max-w-2xl text-sm text-slate-500">
          Registro somente-leitura das ações sensíveis do sistema: login/logout, dinheiro mudando de
          mão e mudanças de estoque. Nada aqui pode ser editado ou apagado pela aplicação.
        </p>
        <select value={actionFilter} onChange={e=>setActionFilter(e.target.value)}
          className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm outline-none focus:border-slate-400">
          <option value="">Todas as ações</option>
          {knownActions.map(a => <option key={a} value={a}>{actionLabel[a]}</option>)}
        </select>
      </div>

      <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-soft">
        {loading && <div className="p-6 text-sm text-slate-400">Carregando...</div>}
        {error && <div className="p-6 text-sm text-red-600">{error}</div>}
        {!loading && !error && logs.length === 0 && <div className="p-6 text-sm text-slate-400">Nenhum registro encontrado.</div>}
        {!loading && !error && logs.length > 0 && (
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-left text-xs font-bold uppercase tracking-wider text-slate-400">
              <tr>
                <th className="px-5 py-3">Quando</th><th className="px-5 py-3">Ação</th>
                <th className="px-5 py-3">Entidade</th><th className="px-5 py-3">Detalhe</th><th className="px-5 py-3">IP</th>
              </tr>
            </thead>
            <tbody>
              {logs.map(l => (
                <tr key={l.id} className="border-t border-slate-100">
                  <td className="px-5 py-3 text-xs text-slate-500">{new Date(l.created_at).toLocaleString('pt-BR')}</td>
                  <td className="px-5 py-3 font-semibold">{actionLabel[l.action] ?? l.action}</td>
                  <td className="px-5 py-3 text-xs text-slate-500">{l.entity_type}{l.entity_id != null ? ` #${l.entity_id}` : ''}</td>
                  <td className="px-5 py-3 text-slate-600">{l.detail || '—'}</td>
                  <td className="px-5 py-3 font-mono text-xs text-slate-400">{l.ip_address || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </section>
  )
}

function RetentionPage() {
  const [candidates, setCandidates] = useState<RetentionCandidate[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [actionMessage, setActionMessage] = useState('')
  const [actionError, setActionError] = useState('')
  const [busy, setBusy] = useState(false)

  function reload() {
    setLoading(true); setError('')
    listRetentionCandidates()
      .then(setCandidates)
      .catch(() => setError('Não foi possível carregar os candidatos à retenção.'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { reload() }, [])

  async function handlePurge() {
    setBusy(true); setActionError(''); setActionMessage('')
    try {
      const r = await purgeOldNotifications()
      setActionMessage(`${r.deleted_count} registro(s) de notificação antigos apagados.`)
    } catch {
      setActionError('Não foi possível apagar as notificações antigas.')
    } finally {
      setBusy(false)
    }
  }

  async function handleAnonymizeInactive() {
    if (!window.confirm(`Anonimizar todos os ${candidates.length} clientes inativos listados abaixo? Esta ação não pode ser desfeita.`)) return
    setBusy(true); setActionError(''); setActionMessage('')
    try {
      const r = await anonymizeInactiveCustomers()
      setActionMessage(`${r.anonymized_count} cliente(s) anonimizado(s).`)
      reload()
    } catch {
      setActionError('Não foi possível anonimizar os clientes inativos.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="mx-auto max-w-7xl space-y-6 p-5 md:p-8">
      <p className="max-w-2xl text-sm text-slate-500">
        Ferramentas de minimização de dados (LGPD, art. 6º VII): apagar registros operacionais que
        já não têm valor de guarda, e identificar clientes inativos há muitos anos, sem pendência
        financeira, que são candidatos a anonimização.
      </p>

      <div className="flex flex-wrap gap-3">
        <button disabled={busy} onClick={handlePurge}
          className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-bold text-slate-600 disabled:opacity-50">
          <Trash2 size={16}/> Apagar notificações antigas
        </button>
        <button disabled={busy || candidates.length === 0} onClick={handleAnonymizeInactive}
          className="flex items-center gap-2 rounded-xl bg-slate-950 px-4 py-2 text-sm font-bold text-white disabled:opacity-50">
          <ShieldCheck size={16}/> Anonimizar todos os candidatos
        </button>
      </div>

      {actionMessage && <div className="rounded-xl bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{actionMessage}</div>}
      {actionError && <div className="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-600">{actionError}</div>}

      <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-soft">
        <div className="border-b border-slate-100 p-5 font-black">Candidatos a anonimização por inatividade</div>
        {loading && <div className="p-6 text-sm text-slate-400">Carregando...</div>}
        {error && <div className="p-6 text-sm text-red-600">{error}</div>}
        {!loading && !error && candidates.length === 0 && (
          <div className="p-6 text-sm text-slate-400">Nenhum cliente inativo encontrado no momento.</div>
        )}
        {!loading && !error && candidates.length > 0 && (
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-left text-xs font-bold uppercase tracking-wider text-slate-400">
              <tr><th className="px-5 py-3">Nome</th><th className="px-5 py-3">Última atividade</th><th className="px-5 py-3">Cliente desde</th></tr>
            </thead>
            <tbody>
              {candidates.map(cand => (
                <tr key={cand.id} className="border-t border-slate-100">
                  <td className="px-5 py-3 font-semibold">{cand.name}</td>
                  <td className="px-5 py-3 text-slate-500">{cand.last_activity_at ? new Date(cand.last_activity_at).toLocaleDateString('pt-BR') : 'nunca'}</td>
                  <td className="px-5 py-3 text-slate-500">{new Date(cand.created_at).toLocaleDateString('pt-BR')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </section>
  )
}

const queueStatusLabel: Record<string, string> = {
  PENDING: 'Aguardando novo envio', SENT: 'Enviado', SKIPPED: 'Ignorado', FAILED: 'Falhou (será retentado)', GIVEN_UP: 'Desistiu',
}
const queueStatusColor: Record<string, string> = {
  PENDING: 'bg-amber-50 text-amber-600', SENT: 'bg-emerald-50 text-emerald-600',
  SKIPPED: 'bg-slate-100 text-slate-400', FAILED: 'bg-amber-50 text-amber-600', GIVEN_UP: 'bg-red-50 text-red-500',
}

function NotificationQueuePage() {
  const [entries, setEntries] = useState<NotificationQueueEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [actionMessage, setActionMessage] = useState('')
  const [busy, setBusy] = useState(false)

  function reload() {
    setLoading(true); setError('')
    listNotificationQueue()
      .then(setEntries)
      .catch(() => setError('Não foi possível carregar a fila de notificações.'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { reload() }, [])

  async function handleProcess() {
    setBusy(true); setActionMessage('')
    try {
      const r = await processNotificationQueue()
      setActionMessage(`${r.sent} enviado(s), ${r.failed_retry} vão ser retentados, ${r.given_up} desistido(s).`)
      reload()
    } catch {
      setActionMessage('Não foi possível reprocessar a fila agora.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="mx-auto max-w-7xl space-y-6 p-5 md:p-8">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <p className="max-w-2xl text-sm text-slate-500">
          Comprovantes e lembretes que falharam no envio imediato entram aqui para reenvio
          automático, com backoff crescente e sem duplicar (idempotência). Só chegam aqui falhas
          reais — sem SMTP/WhatsApp configurado, o envio fica apenas "Ignorado", sem entrar na fila.
        </p>
        <button disabled={busy} onClick={handleProcess}
          className="flex items-center gap-2 rounded-xl bg-slate-950 px-4 py-2 text-sm font-bold text-white disabled:opacity-50">
          <RefreshCw size={16}/> Reprocessar fila agora
        </button>
      </div>

      {actionMessage && <div className="rounded-xl bg-slate-50 px-4 py-3 text-sm text-slate-600">{actionMessage}</div>}

      <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-soft">
        {loading && <div className="p-6 text-sm text-slate-400">Carregando...</div>}
        {error && <div className="p-6 text-sm text-red-600">{error}</div>}
        {!loading && !error && entries.length === 0 && (
          <div className="p-6 text-sm text-slate-400">Fila vazia — nenhuma notificação precisou de reenvio.</div>
        )}
        {!loading && !error && entries.length > 0 && (
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-left text-xs font-bold uppercase tracking-wider text-slate-400">
              <tr>
                <th className="px-5 py-3">Canal</th><th className="px-5 py-3">Status</th>
                <th className="px-5 py-3">Tentativas</th><th className="px-5 py-3">Próxima tentativa</th>
                <th className="px-5 py-3">Último erro</th>
              </tr>
            </thead>
            <tbody>
              {entries.map(e => (
                <tr key={e.id} className="border-t border-slate-100">
                  <td className="px-5 py-3 text-xs font-bold text-slate-500">{e.channel === 'EMAIL' ? 'E-mail' : 'WhatsApp'}</td>
                  <td className="px-5 py-3">
                    <span className={`rounded-full px-2.5 py-1 text-xs font-bold ${queueStatusColor[e.status]}`}>{queueStatusLabel[e.status]}</span>
                  </td>
                  <td className="px-5 py-3 text-slate-500">{e.attempts} / {e.max_attempts}</td>
                  <td className="px-5 py-3 text-xs text-slate-500">{new Date(e.next_attempt_at).toLocaleString('pt-BR')}</td>
                  <td className="px-5 py-3 text-slate-600">{e.last_error || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </section>
  )
}

function App() {
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState<any>(null)
  const [busy, setBusy] = useState(false)
  const [upload, setUpload] = useState('')
  const [authChecked, setAuthChecked] = useState(false)
  const [currentUser, setCurrentUser] = useState<any>(null)
  const [page, setPage] = useState<Page>('dashboard')
  const [homeStats, setHomeStats] = useState<DashboardReport | null>(null)

  useEffect(() => {
    me().then(setCurrentUser).catch(() => setCurrentUser(null)).finally(() => setAuthChecked(true))
  }, [])

  useEffect(() => {
    if (page === 'dashboard' && currentUser) {
      getDashboardReport().then(setHomeStats).catch(() => setHomeStats(null))
    }
  }, [page, currentUser])

  if (!authChecked) return null
  if (!currentUser) return <LoginScreen onLoggedIn={() => me().then(setCurrentUser)} />

  async function handleLogout() {
    await logout().catch(() => {})
    setCurrentUser(null)
  }

  async function ask() {
    if (!question.trim()) return
    setBusy(true)
    try { setAnswer(await askAI(question)) } catch (e:any) { setAnswer({answer:e.message, source:'error'}) }
    finally { setBusy(false) }
  }

  async function handleFile(file?: File) {
    if (!file) return
    setUpload('Processando OCR/RAG...')
    try {
      const r = await ingestFile(file)
      setUpload(`${r.filename} indexado em ${r.chunks} chunks.`)
    } catch (e:any) { setUpload(e.message) }
  }

  return (
    <div className="min-h-screen bg-[#f6f8fb]">
      <aside className="fixed inset-y-0 left-0 hidden w-64 border-r border-slate-200 bg-white lg:flex lg:flex-col">
        <div className="flex items-center gap-3 px-6 py-6">
          <div className="grid h-10 w-10 place-items-center rounded-2xl bg-slate-950 text-white"><Wrench size={19}/></div>
          <div><div className="font-black tracking-tight">Oficina AI</div><div className="text-xs text-slate-400">Ops Intelligence</div></div>
        </div>
        <nav className="space-y-1 px-3">
          {nav.map(([label, Icon, target]) => {
            const active = page === target
            return (
              <button key={label} onClick={() => setPage(target)}
                className={`flex w-full items-center gap-3 rounded-xl px-3 py-3 text-sm ${active ? 'bg-slate-950 text-white' : 'text-slate-600 hover:bg-slate-100'}`}>
                <Icon size={17}/>{label}<ChevronRight size={14} className="ml-auto opacity-40"/>
              </button>
            )
          })}
        </nav>
        <div className="mt-auto p-4"><button className="flex w-full items-center gap-3 rounded-xl px-3 py-3 text-sm text-slate-500 hover:bg-slate-100"><Settings size={17}/>Configurações</button></div>
      </aside>

      <main className="lg:pl-64">
        <header className="sticky top-0 z-10 flex h-20 items-center justify-between border-b border-slate-200/80 bg-white/90 px-5 backdrop-blur md:px-8">
          <div><div className="text-xs font-semibold uppercase tracking-[.18em] text-slate-400">{pageEyebrow[page]}</div><h1 className="text-xl font-black">{pageTitle[page]}</h1></div>
          <div className="flex items-center gap-3">
            <button className="rounded-xl border border-slate-200 bg-white p-2.5"><Search size={18}/></button>
            <span className="hidden text-sm text-slate-500 md:inline">{currentUser?.name}</span>
            <button onClick={handleLogout} title="Sair" className="rounded-xl border border-slate-200 bg-white p-2.5"><LogOut size={18}/></button>
          </div>
        </header>

        {page === 'customers' ? <CustomersPage /> : page === 'agenda' ? <AgendaPage />
        : page === 'stock' ? <StockPage /> : page === 'workorders' ? <WorkOrdersPage />
        : page === 'reports' ? <ReportsPage /> : page === 'finance' ? <FinancePage />
        : page === 'purchases' ? <PurchasesPage /> : page === 'audit' ? <AuditPage />
        : page === 'retention' ? <RetentionPage /> : page === 'notifqueue' ? <NotificationQueuePage /> : (
        <section className="mx-auto max-w-7xl space-y-6 p-5 md:p-8">
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {[
              ['OS abertas', homeStats ? String(homeStats.open_work_orders) : '—', 'não concluídas nem canceladas'],
              ['Valor em estoque', homeStats ? `R$ ${homeStats.stock_value.toFixed(2)}` : '—', homeStats ? `${homeStats.stock_critical_items} itens críticos` : 'sem dados'],
              ['Lucro do mês', homeStats ? `R$ ${homeStats.profit_this_month.toFixed(2)}` : '—', homeStats ? `mês anterior: R$ ${homeStats.profit_last_month.toFixed(2)}` : 'sem dados'],
              ['Clientes', homeStats ? String(homeStats.customers_total) : '—', homeStats ? `+${homeStats.customers_new_this_month} este mês` : 'sem dados'],
            ].map(([a,b,c]) => <div key={a} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-soft"><div className="text-sm text-slate-500">{a}</div><div className="mt-2 text-3xl font-black">{b}</div><div className="mt-2 text-xs font-semibold text-slate-400">{c}</div></div>)}
          </div>

          <div className="grid gap-6 xl:grid-cols-[1.6fr_1fr]">
            <div className="rounded-3xl bg-slate-950 p-6 text-white shadow-soft md:p-8">
              <div className="mb-8 flex items-start justify-between"><div><div className="mb-2 flex items-center gap-2 text-xs font-bold uppercase tracking-[.2em] text-slate-400"><Sparkles size={14}/> Oficina Copilot</div><h2 className="max-w-xl text-2xl font-black md:text-3xl">Pergunte sobre clientes, veículos, OS e documentos.</h2></div><Bot size={25} className="text-slate-400"/></div>
              <div className="rounded-2xl bg-white/10 p-2 ring-1 ring-white/10"><textarea value={question} onChange={e=>setQuestion(e.target.value)} onKeyDown={e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();ask()}}} placeholder="Ex.: quais serviços aparecem no manual enviado?" className="min-h-28 w-full resize-none bg-transparent p-3 text-sm outline-none placeholder:text-slate-500"/><div className="flex justify-end"><button onClick={ask} disabled={busy} className="rounded-xl bg-white px-4 py-2 text-sm font-bold text-slate-950 disabled:opacity-50">{busy?'Consultando...':'Consultar IA'}</button></div></div>
              {answer && <div className="mt-4 rounded-2xl bg-white p-5 text-sm text-slate-800"><div className="mb-2 flex gap-2 text-xs font-bold uppercase tracking-wider text-slate-400"><Activity size={14}/> {answer.source} · {answer.provider || 'local'} · {answer.chunks_used ?? 0} chunks</div><p className="whitespace-pre-wrap">{answer.answer}</p></div>}
            </div>

            <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-soft">
              <div className="flex items-center justify-between"><div><h2 className="font-black">OCR + RAG</h2><p className="mt-1 text-sm text-slate-500">Envie PDF ou imagem para indexar.</p></div><UploadCloud size={21}/></div>
              <label className="mt-6 flex cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed border-slate-200 bg-slate-50 p-8 text-center hover:bg-slate-100">
                <UploadCloud className="mb-3 text-slate-400"/><span className="text-sm font-bold">Selecionar documento</span><span className="mt-1 text-xs text-slate-400">PDF, PNG, JPG ou TXT</span>
                <input type="file" className="hidden" onChange={e=>handleFile(e.target.files?.[0])}/>
              </label>
              {upload && <div className="mt-4 rounded-xl bg-slate-100 p-3 text-xs text-slate-600">{upload}</div>}
              <div className="mt-6 grid grid-cols-3 gap-2 text-center text-xs"><div className="rounded-xl bg-slate-50 p-3"><b className="block text-base">01</b>Upload</div><div className="rounded-xl bg-slate-50 p-3"><b className="block text-base">02</b>OCR</div><div className="rounded-xl bg-slate-50 p-3"><b className="block text-base">03</b>RAG</div></div>
            </div>
          </div>

          <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-soft">
            <div className="flex items-center justify-between"><div><h2 className="font-black">Arquitetura AI</h2><p className="mt-1 text-sm text-slate-500">Memória primeiro → RAG → LLM somente quando necessário.</p></div><div className="rounded-xl bg-slate-100 p-3"><Bot size={18}/></div></div>
            <div className="mt-5 grid gap-3 md:grid-cols-4">{[['01','Memory','Teste conhecido não consome token.'],['02','RAG','Busca local nos documentos.'],['03','Gateway','Escolhe o provedor configurado.'],['04','Auditável','Fonte e chunks retornados.']].map(([n,t,d])=><div key={n} className="rounded-2xl border border-slate-100 p-4"><div className="text-xs font-black text-slate-300">{n}</div><div className="mt-2 font-bold">{t}</div><p className="mt-1 text-xs leading-5 text-slate-500">{d}</p></div>)}</div>
          </div>
        </section>
        )}
      </main>
    </div>
  )
}

export default App
