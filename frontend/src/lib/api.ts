const API = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

// A partir da FASE 1, a autenticação é por sessão via cookie httpOnly
// (definido pelo backend em /api/auth/login). `credentials: 'include'` é
// obrigatório em toda chamada para que o navegador envie/receba esse cookie
// — sem isso, o backend responde 401 mesmo com login válido.

export async function login(email: string, password: string) {
  const r = await fetch(`${API}/auth/login`, {
    method: 'POST',
    credentials: 'include',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({email, password})
  })
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}

export async function logout() {
  const r = await fetch(`${API}/auth/logout`, {method:'POST', credentials:'include'})
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}

export async function me() {
  const r = await fetch(`${API}/auth/me`, {credentials:'include'})
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}

export async function askAI(question: string) {
  const r = await fetch(`${API}/ai/ask`, {
    method: 'POST',
    credentials: 'include',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({question, use_rag:true, memory_first:true})
  })
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}

export type Vehicle = {
  id: number
  customer_id: number
  plate: string
  brand: string
  model: string
  year: number | null
  color: string
  km: number | null
  notes: string
  is_active: boolean
  created_at: string
}

export type CustomerListItem = {
  id: number
  name: string
  document: string
  phone: string
  email: string
  is_active: boolean
  is_anonymized: boolean
  vehicle_count: number
  created_at: string
}

export type Customer = Omit<CustomerListItem, 'vehicle_count'> & {
  address: string
  notes: string
  vehicles: Vehicle[]
}

async function handle<T>(r: Response): Promise<T> {
  if (!r.ok) throw new Error(await r.text())
  return r.status === 204 ? (undefined as T) : r.json()
}

export async function listCustomers(q?: string): Promise<CustomerListItem[]> {
  const query = q ? `?q=${encodeURIComponent(q)}` : ''
  const r = await fetch(`${API}/customers${query}`, { credentials: 'include' })
  return handle(r)
}

export async function getCustomer(id: number): Promise<Customer> {
  const r = await fetch(`${API}/customers/${id}`, { credentials: 'include' })
  return handle(r)
}

export async function createCustomer(payload: {
  name: string; document?: string; phone?: string; email?: string; address?: string; notes?: string
  vehicles?: { plate: string; brand?: string; model?: string; year?: number; color?: string }[]
}): Promise<Customer> {
  const r = await fetch(`${API}/customers`, {
    method: 'POST', credentials: 'include',
    headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
  })
  return handle(r)
}

export async function updateCustomer(id: number, payload: Partial<{
  name: string; document: string; phone: string; email: string; address: string; notes: string; is_active: boolean
}>): Promise<Customer> {
  const r = await fetch(`${API}/customers/${id}`, {
    method: 'PATCH', credentials: 'include',
    headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
  })
  return handle(r)
}

export async function deleteCustomer(id: number): Promise<void> {
  const r = await fetch(`${API}/customers/${id}`, { method: 'DELETE', credentials: 'include' })
  return handle(r)
}

export async function addVehicle(customerId: number, payload: {
  plate: string; brand?: string; model?: string; year?: number; color?: string; km?: number
}): Promise<Vehicle> {
  const r = await fetch(`${API}/customers/${customerId}/vehicles`, {
    method: 'POST', credentials: 'include',
    headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
  })
  return handle(r)
}

export type AppointmentStatus = 'SCHEDULED' | 'CONFIRMED' | 'IN_PROGRESS' | 'DONE' | 'CANCELLED' | 'NO_SHOW'

export type Appointment = {
  id: number
  company_id: number
  branch_id: number | null
  customer_id: number
  vehicle_id: number | null
  mechanic_id: number | null
  scheduled_at: string
  duration_minutes: number
  status: AppointmentStatus
  service_type: string
  notes: string
  created_at: string
  customer_name: string
  vehicle_plate: string
}

export async function listAppointments(params?: { date_from?: string; date_to?: string }): Promise<Appointment[]> {
  const query = new URLSearchParams()
  if (params?.date_from) query.set('date_from', params.date_from)
  if (params?.date_to) query.set('date_to', params.date_to)
  const qs = query.toString()
  const r = await fetch(`${API}/appointments${qs ? `?${qs}` : ''}`, { credentials: 'include' })
  return handle(r)
}

export async function createAppointment(payload: {
  customer_id: number; vehicle_id?: number; scheduled_at: string
  duration_minutes?: number; service_type?: string; notes?: string
}): Promise<Appointment> {
  const r = await fetch(`${API}/appointments`, {
    method: 'POST', credentials: 'include',
    headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
  })
  return handle(r)
}

export async function cancelAppointment(id: number): Promise<Appointment> {
  const r = await fetch(`${API}/appointments/${id}/cancel`, { method: 'POST', credentials: 'include' })
  return handle(r)
}

// ------------------------------------------------------------- Estoque

export type StockItem = {
  id: number
  sku: string
  name: string
  unit: string
  quantity: number
  min_quantity: number
  cost_price: number
  sale_price: number
  notes: string
  is_active: boolean
  is_low_stock: boolean
  created_at: string
}

export async function listStock(params?: { q?: string; onlyLowStock?: boolean }): Promise<StockItem[]> {
  const query = new URLSearchParams()
  if (params?.q) query.set('q', params.q)
  if (params?.onlyLowStock) query.set('only_low_stock', 'true')
  const qs = query.toString()
  const r = await fetch(`${API}/stock${qs ? `?${qs}` : ''}`, { credentials: 'include' })
  return handle(r)
}

export async function createStockItem(payload: {
  sku: string; name: string; unit?: string; quantity?: number; min_quantity?: number
  cost_price?: number; sale_price?: number; notes?: string
}): Promise<StockItem> {
  const r = await fetch(`${API}/stock`, {
    method: 'POST', credentials: 'include',
    headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
  })
  return handle(r)
}

export async function adjustStockItem(id: number, payload: { type: 'IN' | 'OUT' | 'ADJUSTMENT'; quantity: number; reason?: string }): Promise<StockItem> {
  const r = await fetch(`${API}/stock/${id}/adjust`, {
    method: 'POST', credentials: 'include',
    headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
  })
  return handle(r)
}

// --------------------------------------------------- Ordens de serviço

export type WorkOrderStatus = 'OPEN' | 'IN_PROGRESS' | 'AWAITING_APPROVAL' | 'APPROVED' | 'DONE' | 'CANCELLED'

export type WorkOrderItem = {
  id: number
  kind: 'PART' | 'SERVICE'
  description: string
  stock_item_id: number | null
  quantity: number
  unit_price: number
  total_price: number
}

export type WorkOrder = {
  id: number
  company_id: number
  branch_id: number | null
  customer_id: number
  vehicle_id: number | null
  appointment_id: number | null
  mechanic_id: number | null
  status: WorkOrderStatus
  description: string
  diagnosis: string
  labor_value: number
  discount_value: number
  total_value: number
  next_revision_date: string | null
  created_at: string
  closed_at: string | null
  customer_name: string
  vehicle_plate: string
  items: WorkOrderItem[]
}

export async function listWorkOrders(params?: { status?: WorkOrderStatus }): Promise<WorkOrder[]> {
  const query = new URLSearchParams()
  if (params?.status) query.set('status', params.status)
  const qs = query.toString()
  const r = await fetch(`${API}/work-orders${qs ? `?${qs}` : ''}`, { credentials: 'include' })
  return handle(r)
}

export async function createWorkOrder(payload: {
  customer_id: number; vehicle_id?: number; description?: string; diagnosis?: string
  labor_value?: number; discount_value?: number; next_revision_date?: string
  items?: { kind: 'PART' | 'SERVICE'; description: string; stock_item_id?: number; quantity?: number; unit_price?: number }[]
}): Promise<WorkOrder> {
  const r = await fetch(`${API}/work-orders`, {
    method: 'POST', credentials: 'include',
    headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
  })
  return handle(r)
}

export async function closeWorkOrder(id: number): Promise<WorkOrder> {
  const r = await fetch(`${API}/work-orders/${id}/close`, { method: 'POST', credentials: 'include' })
  return handle(r)
}

export async function cancelWorkOrder(id: number): Promise<WorkOrder> {
  const r = await fetch(`${API}/work-orders/${id}/cancel`, { method: 'POST', credentials: 'include' })
  return handle(r)
}

// ------------------------------------------------------------ Relatórios

export type MonthlyPoint = { month: string; revenue: number; profit: number; work_orders_closed: number }

export type DashboardReport = {
  stock_value: number
  stock_critical_items: number
  open_work_orders: number
  customers_total: number
  customers_new_this_month: number
  revenue_this_month: number
  profit_this_month: number
  revenue_last_month: number
  profit_last_month: number
  receivables_pending: number
  payables_pending: number
  cash_balance: number | null
  monthly_series: MonthlyPoint[]
}

export async function getDashboardReport(): Promise<DashboardReport> {
  const r = await fetch(`${API}/reports/dashboard`, { credentials: 'include' })
  return handle(r)
}

// -------------------------------------------------------- Financeiro/Caixa

export type FinanceEntryType = 'PAYABLE' | 'RECEIVABLE'
export type FinanceEntryStatus = 'PENDING' | 'PAID' | 'OVERDUE' | 'CANCELLED'

export type FinanceEntry = {
  id: number
  type: FinanceEntryType
  status: FinanceEntryStatus
  category: string
  description: string
  amount: number
  due_date: string
  paid_amount: number
  remaining_amount: number
  paid_at: string | null
  customer_id: number | null
  customer_name: string
  work_order_id: number | null
  created_at: string
}

export async function listFinanceEntries(params?: { type?: FinanceEntryType; status?: FinanceEntryStatus }): Promise<FinanceEntry[]> {
  const query = new URLSearchParams()
  if (params?.type) query.set('type', params.type)
  if (params?.status) query.set('status', params.status)
  const qs = query.toString()
  const r = await fetch(`${API}/finance/entries${qs ? `?${qs}` : ''}`, { credentials: 'include' })
  return handle(r)
}

export async function createFinanceEntry(payload: {
  type: FinanceEntryType; category?: string; description?: string; amount: number; due_date: string; customer_id?: number
}): Promise<FinanceEntry> {
  const r = await fetch(`${API}/finance/entries`, {
    method: 'POST', credentials: 'include',
    headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
  })
  return handle(r)
}

export async function payFinanceEntry(id: number, amount?: number): Promise<FinanceEntry> {
  const r = await fetch(`${API}/finance/entries/${id}/pay`, {
    method: 'POST', credentials: 'include',
    headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(amount != null ? { amount } : {})
  })
  return handle(r)
}

export async function cancelFinanceEntry(id: number): Promise<FinanceEntry> {
  const r = await fetch(`${API}/finance/entries/${id}/cancel`, { method: 'POST', credentials: 'include' })
  return handle(r)
}

export type CashSession = {
  id: number
  status: 'OPEN' | 'CLOSED'
  opening_amount: number
  opened_at: string
  closing_amount_expected: number | null
  closing_amount_counted: number | null
  cash_difference: number | null
  closed_at: string | null
  notes: string
  current_balance: number
}

export type CashMovement = {
  id: number
  type: 'IN' | 'OUT'
  amount: number
  description: string
  finance_entry_id: number | null
  created_at: string
}

export async function getCurrentCashSession(): Promise<CashSession | null> {
  const r = await fetch(`${API}/cash/sessions/current`, { credentials: 'include' })
  return handle(r)
}

export async function listCashSessions(): Promise<CashSession[]> {
  const r = await fetch(`${API}/cash/sessions`, { credentials: 'include' })
  return handle(r)
}

export async function openCashSession(opening_amount: number, notes?: string): Promise<CashSession> {
  const r = await fetch(`${API}/cash/sessions/open`, {
    method: 'POST', credentials: 'include',
    headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ opening_amount, notes })
  })
  return handle(r)
}

export async function closeCashSession(id: number, closing_amount_counted: number, notes?: string): Promise<CashSession> {
  const r = await fetch(`${API}/cash/sessions/${id}/close`, {
    method: 'POST', credentials: 'include',
    headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ closing_amount_counted, notes })
  })
  return handle(r)
}

export async function listCashMovements(sessionId: number): Promise<CashMovement[]> {
  const r = await fetch(`${API}/cash/sessions/${sessionId}/movements`, { credentials: 'include' })
  return handle(r)
}

export async function addCashMovement(sessionId: number, payload: { type: 'IN' | 'OUT'; amount: number; description?: string }): Promise<CashMovement> {
  const r = await fetch(`${API}/cash/sessions/${sessionId}/movements`, {
    method: 'POST', credentials: 'include',
    headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
  })
  return handle(r)
}

// ------------------------------------------------- Fornecedores e Compras

export type Supplier = {
  id: number
  name: string
  document: string
  phone: string
  email: string
  notes: string
  is_active: boolean
  created_at: string
}

export async function listSuppliers(q?: string): Promise<Supplier[]> {
  const query = q ? `?q=${encodeURIComponent(q)}` : ''
  const r = await fetch(`${API}/suppliers${query}`, { credentials: 'include' })
  return handle(r)
}

export async function createSupplier(payload: { name: string; document?: string; phone?: string; email?: string; notes?: string }): Promise<Supplier> {
  const r = await fetch(`${API}/suppliers`, {
    method: 'POST', credentials: 'include',
    headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
  })
  return handle(r)
}

export type PurchaseOrderStatus = 'DRAFT' | 'ORDERED' | 'RECEIVED' | 'CANCELLED'

export type PurchaseOrderItem = {
  id: number
  description: string
  stock_item_id: number | null
  quantity: number
  unit_cost: number
  total_cost: number
}

export type PurchaseOrder = {
  id: number
  supplier_id: number
  supplier_name: string
  status: PurchaseOrderStatus
  notes: string
  payment_due_date: string | null
  total_value: number
  created_at: string
  ordered_at: string | null
  received_at: string | null
  items: PurchaseOrderItem[]
}

export async function listPurchaseOrders(params?: { status?: PurchaseOrderStatus }): Promise<PurchaseOrder[]> {
  const query = new URLSearchParams()
  if (params?.status) query.set('status', params.status)
  const qs = query.toString()
  const r = await fetch(`${API}/purchase-orders${qs ? `?${qs}` : ''}`, { credentials: 'include' })
  return handle(r)
}

export async function createPurchaseOrder(payload: {
  supplier_id: number; notes?: string; payment_due_date?: string
  items?: { description: string; stock_item_id?: number; quantity?: number; unit_cost?: number }[]
}): Promise<PurchaseOrder> {
  const r = await fetch(`${API}/purchase-orders`, {
    method: 'POST', credentials: 'include',
    headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
  })
  return handle(r)
}

export async function receivePurchaseOrder(id: number): Promise<PurchaseOrder> {
  const r = await fetch(`${API}/purchase-orders/${id}/receive`, { method: 'POST', credentials: 'include' })
  return handle(r)
}

export async function cancelPurchaseOrder(id: number): Promise<PurchaseOrder> {
  const r = await fetch(`${API}/purchase-orders/${id}/cancel`, { method: 'POST', credentials: 'include' })
  return handle(r)
}

// ------------------------------------------------------------- Auditoria

export type AuditLog = {
  id: number
  user_id: number | null
  action: string
  entity_type: string
  entity_id: number | null
  detail: string
  ip_address: string
  created_at: string
}

export async function listAuditLogs(params?: { action?: string; entity_type?: string }): Promise<AuditLog[]> {
  const query = new URLSearchParams()
  if (params?.action) query.set('action', params.action)
  if (params?.entity_type) query.set('entity_type', params.entity_type)
  const qs = query.toString()
  const r = await fetch(`${API}/audit-logs${qs ? `?${qs}` : ''}`, { credentials: 'include' })
  return handle(r)
}

// ------------------------------------------------------------------ LGPD

export async function exportCustomerData(customerId: number): Promise<any> {
  const r = await fetch(`${API}/customers/${customerId}/export-data`, { credentials: 'include' })
  return handle(r)
}

export async function anonymizeCustomer(customerId: number): Promise<{ id: number; is_anonymized: boolean; anonymized_at: string | null }> {
  const r = await fetch(`${API}/customers/${customerId}/anonymize`, { method: 'POST', credentials: 'include' })
  return handle(r)
}

// -------------------------------------------------------------- Retenção

export type RetentionCandidate = {
  id: number
  name: string
  last_activity_at: string | null
  created_at: string
}

export async function listRetentionCandidates(): Promise<RetentionCandidate[]> {
  const r = await fetch(`${API}/retention/candidates`, { credentials: 'include' })
  return handle(r)
}

export async function purgeOldNotifications(): Promise<{ deleted_count: number }> {
  const r = await fetch(`${API}/retention/purge-notifications`, { method: 'POST', credentials: 'include' })
  return handle(r)
}

export async function anonymizeInactiveCustomers(): Promise<{ anonymized_count: number; customer_ids: number[] }> {
  const r = await fetch(`${API}/retention/anonymize-inactive`, { method: 'POST', credentials: 'include' })
  return handle(r)
}

// ------------------------------------------------- Fila de notificações

export type NotificationQueueStatus = 'PENDING' | 'SENT' | 'SKIPPED' | 'FAILED' | 'GIVEN_UP'

export type NotificationQueueEntry = {
  id: number
  idempotency_key: string
  channel: string
  type: string
  status: NotificationQueueStatus
  customer_id: number | null
  work_order_id: number | null
  attempts: number
  max_attempts: number
  next_attempt_at: string
  last_error: string
  created_at: string
}

export async function listNotificationQueue(): Promise<NotificationQueueEntry[]> {
  const r = await fetch(`${API}/notifications/queue`, { credentials: 'include' })
  return handle(r)
}

export async function processNotificationQueue(): Promise<{ sent: number; failed_retry: number; given_up: number }> {
  const r = await fetch(`${API}/notifications/process-queue`, { method: 'POST', credentials: 'include' })
  return handle(r)
}

export async function ingestFile(file: File) {
  const form = new FormData()
  form.append('file', file)
  const r = await fetch(`${API}/rag/ingest`, {method:'POST', credentials:'include', body:form})
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}
