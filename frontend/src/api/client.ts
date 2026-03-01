const API_BASE = '/api/v1';

class ApiClient {
  private token: string | null = null;

  setToken(token: string) {
    this.token = token;
    localStorage.setItem('towerops_token', token);
  }

  loadToken() {
    this.token = localStorage.getItem('towerops_token');
    return this.token;
  }

  clearToken() {
    this.token = null;
    localStorage.removeItem('towerops_token');
  }

  private async request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string>),
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

    if (res.status === 401) {
      this.clearToken();
      window.location.href = '/login';
      throw new Error('Unauthorized');
    }

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Request failed' }));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }

    return res.json();
  }

  // Auth
  login(email: string, password: string) {
    return this.request<{ access_token: string }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
  }

  register(name: string, email: string, password: string, adminName: string) {
    return this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify({
        name,
        admin_email: email,
        admin_password: password,
        admin_name: adminName,
      }),
    });
  }

  getMe() {
    return this.request('/auth/me');
  }

  // Dashboard
  getDashboardStats() {
    return this.request('/dashboard/stats');
  }

  getDashboardProjects() {
    return this.request('/dashboard/projects');
  }

  // Projects
  getProjects(params?: { status?: string; carrier?: string }) {
    const query = new URLSearchParams(params as Record<string, string>).toString();
    return this.request(`/projects/${query ? `?${query}` : ''}`);
  }

  getProject(id: string) {
    return this.request(`/projects/${id}`);
  }

  createProject(data: Record<string, unknown>) {
    return this.request('/projects/', { method: 'POST', body: JSON.stringify(data) });
  }

  updateProject(id: string, data: Record<string, unknown>) {
    return this.request(`/projects/${id}`, { method: 'PATCH', body: JSON.stringify(data) });
  }

  // Budget
  getProjectBudget(projectId: string) {
    return this.request(`/projects/${projectId}/budget`);
  }

  addBudgetLine(projectId: string, data: Record<string, unknown>) {
    return this.request(`/projects/${projectId}/budget`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }
}

export const api = new ApiClient();
