// API服务 - 统一管理所有API接口
// 自动检测环境：本地开发使用localhost，生产环境使用服务器地址
const getApiBaseUrl = () => {
    const hostname = window.location.hostname;
    const protocol = window.location.protocol;
    const port = window.location.port;
    
    // 本地开发环境
    if (hostname === 'localhost' || hostname === '127.0.0.1' || hostname === '') {
        return 'http://localhost:5000/api/v1';
    }
    
    // 生产环境：使用当前域名
    return `${protocol}//${hostname}${port ? ':' + port : ''}/api/v1`;
};

const API_BASE_URL = getApiBaseUrl();

// API响应格式
class APIResponse {
  constructor(success, data, message = '') {
    this.success = success;
    this.data = data;
    this.message = message;
    this.timestamp = new Date().toISOString();
  }
}

// 模拟延迟
const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

// API服务类
class APIService {
  constructor() {
    this.token = localStorage.getItem('admin_token') || '';
    this.userInfo = JSON.parse(localStorage.getItem('admin_user') || 'null');
  }

  // 通用请求方法
  async request(url, options = {}) {
    // 构建查询参数
    let fullUrl = `${API_BASE_URL}${url}`;
    if (options.params) {
      const params = new URLSearchParams();
      Object.keys(options.params).forEach(key => {
        if (options.params[key] !== undefined && options.params[key] !== null && options.params[key] !== '') {
          params.append(key, options.params[key]);
        }
      });
      if (params.toString()) {
        fullUrl += '?' + params.toString();
      }
    }
    
    const config = {
      method: options.method || 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...(this.token && { 'Authorization': `Bearer ${this.token}` }),
        ...options.headers
      }
    };
    
    if (options.body) {
      config.body = typeof options.body === 'string' ? options.body : JSON.stringify(options.body);
    }

    try {
      const response = await fetch(fullUrl, config);
      
      // 检查响应状态
      if (!response.ok) {
        let errorMessage = '请求失败';
        let errorData = null;
        try {
          errorData = await response.json();
          errorMessage = errorData.message || errorMessage;
        } catch (e) {
          errorMessage = `HTTP ${response.status}: ${response.statusText}`;
        }
        
        // 如果401，清除token
        if (response.status === 401) {
          this.logout();
        }
        
        return {
          success: false,
          message: errorMessage,
          data: null
        };
      }
      
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('API请求失败:', error);
      // 如果是网络错误，提供更详细的错误信息
      let errorMessage = error.message || '网络请求失败';
      if (error.message === 'Failed to fetch') {
        errorMessage = '无法连接到服务器，请检查后端服务是否运行';
      }
      return {
        success: false,
        message: errorMessage,
        data: null
      };
    }
  }

  // 模拟响应（实际使用时应该删除）
  mockResponse(url, config) {
    // 根据URL返回不同的模拟数据
    if (url.includes('/login')) {
      return this.mockLogin(config);
    } else if (url.includes('/members')) {
      return this.mockMembers(config);
    } else if (url.includes('/agents')) {
      return this.mockAgents(config);
    } else if (url.includes('/orders')) {
      return this.mockOrders(config);
    } else if (url.includes('/transactions')) {
      return this.mockTransactions(config);
    } else if (url.includes('/exceptions')) {
      return this.mockExceptions(config);
    } else if (url.includes('/settings')) {
      return this.mockSettings(config);
    }
    return new APIResponse(true, {});
  }

  // 管理员登录
  async login(username, password) {
    const response = await this.request('/admin/login', {
      method: 'POST',
      body: { username, password }
    });
    
    if (response.success && response.data) {
      this.token = response.data.token;
      this.userInfo = response.data.user;
      localStorage.setItem('admin_token', this.token);
      localStorage.setItem('admin_user', JSON.stringify(this.userInfo));
    }
    
    return response;
  }

  // 登出
  logout() {
    this.token = '';
    this.userInfo = null;
    localStorage.removeItem('admin_token');
    localStorage.removeItem('admin_user');
  }

  // 检查登录状态
  isAuthenticated() {
    return !!this.token;
  }

  // 获取会员列表
  async getMembers(params = {}) {
    return await this.request('/admin/members', {
      method: 'GET',
      params
    });
  }

  // 获取代理列表
  async getAgents(params = {}) {
    return await this.request('/admin/agents', {
      method: 'GET',
      params
    });
  }

  // 创建代理
  async createAgent(data) {
    return await this.request('/admin/agents', {
      method: 'POST',
      body: data
    });
  }

  // 获取报单列表
  async getOrders(params = {}) {
    return await this.request('/admin/orders', {
      method: 'GET',
      params
    });
  }

  // 导出订单
  async exportOrders(orderIds) {
    return await this.request('/admin/orders/export', {
      method: 'POST',
      body: { orderIds }
    });
  }

  // 获取交易记录
  async getTransactions(params = {}) {
    return await this.request('/admin/transactions', {
      method: 'GET',
      params
    });
  }

  // 获取异常订单
  async getExceptions(params = {}) {
    return await this.request('/admin/exceptions', {
      method: 'GET',
      params
    });
  }

  // 导出异常订单
  async exportExceptions(exceptionIds) {
    return await this.request('/admin/exceptions/export', {
      method: 'POST',
      body: { exceptionIds }
    });
  }

  // 获取代理下级
  async getAgentSubordinates(promoCode) {
    return await this.request(`/admin/agents/${promoCode}/subordinates`, {
      method: 'GET'
    });
  }

  // 获取订单统计
  async getOrderStatistics() {
    return await this.request('/admin/statistics/orders', {
      method: 'GET'
    });
  }

  // 获取交易统计
  async getTransactionStatistics() {
    return await this.request('/admin/statistics/transactions', {
      method: 'GET'
    });
  }

  // 获取异常订单统计
  async getExceptionStatistics() {
    return await this.request('/admin/statistics/exceptions', {
      method: 'GET'
    });
  }

  // 删除会员
  async deleteMember(promoCode) {
    return await this.request(`/admin/members/${promoCode}`, {
      method: 'DELETE'
    });
  }

  // 删除代理
  async deleteAgent(promoCode) {
    return await this.request(`/admin/agents/${promoCode}`, {
      method: 'DELETE'
    });
  }

  // 更换上级
  async changeParent(promoCode, parentPromoCode) {
    return await this.request(`/admin/users/${promoCode}/change-parent`, {
      method: 'PUT',
      body: { parentPromoCode }
    });
  }

  // 获取用户订单历史
  async getUserOrders(promoCode, params = {}) {
    return await this.request(`/admin/users/${promoCode}/orders`, {
      method: 'GET',
      params
    });
  }

  // 充值（支持推广码）
  async recharge(promoCode, points, adminPassword) {
    return await this.request('/admin/recharge', {
      method: 'POST',
      body: { promoCode, points, adminPassword }
    });
  }

  // 重置用户登录密码
  async resetUserPassword(promoCode) {
    return await this.request(`/admin/users/${promoCode}/reset-password`, {
      method: 'PUT'
    });
  }

  // 重置用户支付密码
  async resetUserPayPassword(promoCode) {
    return await this.request(`/admin/users/${promoCode}/reset-pay-password`, {
      method: 'PUT'
    });
  }

  // 重置用户登录密码
  async resetUserPassword(promoCode) {
    return await this.request(`/admin/users/${promoCode}/reset-password`, {
      method: 'PUT'
    });
  }

  // 重置用户支付密码
  async resetUserPayPassword(promoCode) {
    return await this.request(`/admin/users/${promoCode}/reset-pay-password`, {
      method: 'PUT'
    });
  }

  // 获取配置
  async getSettings() {
    return await this.request('/admin/settings');
  }

  // 更新配置
  async updateSettings(settings) {
    return await this.request('/admin/settings', {
      method: 'PUT',
      body: settings
    });
  }

  // 模拟登录响应
  mockLogin(config) {
    const body = JSON.parse(config.body || '{}');
    if (body.username === 'admin' && body.password === 'admin123') {
      return new APIResponse(true, {
        token: 'mock_token_' + Date.now(),
        user: {
          id: 1,
          username: 'admin',
          name: '管理员',
          role: 'super_admin'
        }
      });
    }
    return new APIResponse(false, null, '用户名或密码错误');
  }

  // 模拟会员数据
  mockMembers(config) {
    const mockData = {
      list: [
        {
          id: '123456',
          name: '张三',
          phone: '138****1234',
          type: '普通会员',
          parentId: '654321',
          points: 1500,
          registerDate: '2023-01-15',
          nonmemberCount: 8,
          todayOrders: 5,
          monthOrders: 120
        }
      ],
      total: 100,
      page: 1,
      pageSize: 20
    };
    return new APIResponse(true, mockData);
  }

  // 模拟代理数据
  mockAgents(config) {
    const mockData = {
      list: [
        {
          id: '654321',
          name: '王五',
          phone: '137****9012',
          type: '代理',
          parentId: null,
          points: 5000,
          registerDate: '2022-12-01',
          subAgents: 5,
          subMembers: 24,
          nonmemberCount: 15,
          todayOrders: 15,
          monthOrders: 450
        }
      ],
      total: 50,
      page: 1,
      pageSize: 20
    };
    return new APIResponse(true, mockData);
  }

  // 模拟报单数据
  mockOrders(config) {
    return new APIResponse(true, {
      list: [],
      total: 0,
      stats: {
        todayTotal: 156,
        todayUsers: 45,
        todayPoints: 234
      }
    });
  }

  // 模拟交易数据
  mockTransactions(config) {
    return new APIResponse(true, {
      list: [],
      total: 0,
      stats: {
        todayRecharge: 5000,
        todayRevenue: 500,
        todayConsumption: 2340,
        monthRecharge: 50000,
        monthRevenue: 5000,
        monthConsumption: 23400
      }
    });
  }

  // 模拟异常订单数据
  mockExceptions(config) {
    return new APIResponse(true, {
      list: [],
      total: 0,
      stats: {
        todayExceptions: 5,
        todayPending: 3,
        todayProcessed: 2
      }
    });
  }

  // 模拟配置数据
  mockSettings(config) {
    return new APIResponse(true, {
      contact: {
        wechat: 'kefu123456',
        phone: '400-123-4567',
        qq: '123456789'
      },
      price: {
        basePrice: 1,
        fridayPrice: 1.5
      },
      discountRules: [
        { minOrders: 20, discount: 0.4 },
        { minOrders: 10, discount: 0.25 },
        { minOrders: 5, discount: 0.1 }
      ],
      rechargeDiscountRules: [
        { minAmount: 200, discount: 95 },
        { minAmount: 100, discount: 98 }
      ],
      rewardRates: {
        direct: 3,
        indirect: 1
      },
      transferLimits: {
        minQuantity: 10,
        maxUnitPrice: 1.5
      }
    });
  }
}

// 创建全局API实例
const apiService = new APIService();

