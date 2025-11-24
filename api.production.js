// API服务 - 生产环境版本（真实API调用）
const API_BASE_URL = '/api/v1';

// API响应格式
class APIResponse {
  constructor(success, data, message = '') {
    this.success = success;
    this.data = data;
    this.message = message;
    this.timestamp = new Date().toISOString();
  }
}

// API服务类
class APIService {
  constructor() {
    this.token = localStorage.getItem('admin_token') || localStorage.getItem('user_token') || '';
    this.userInfo = JSON.parse(localStorage.getItem('admin_user') || localStorage.getItem('user_info') || 'null');
  }

  // 通用请求方法
  async request(url, options = {}) {
    const config = {
      method: options.method || 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...(this.token && { 'Authorization': `Bearer ${this.token}` }),
        ...options.headers
      }
    };

    // 处理GET请求的查询参数
    if (config.method === 'GET' && options.params) {
      const params = new URLSearchParams();
      Object.keys(options.params).forEach(key => {
        if (options.params[key] !== null && options.params[key] !== undefined && options.params[key] !== '') {
          params.append(key, options.params[key]);
        }
      });
      if (params.toString()) {
        url += '?' + params.toString();
      }
    } else if (options.body) {
      config.body = typeof options.body === 'string' ? options.body : JSON.stringify(options.body);
    }

    try {
      const response = await fetch(`${API_BASE_URL}${url}`, config);
      
      // 处理HTTP错误状态
      if (response.status === 401) {
        // Token过期，清除本地存储并跳转登录
        this.logout();
        if (window.location.pathname.includes('admin')) {
          window.location.reload();
        } else {
          showPage('login-page');
        }
        return new APIResponse(false, null, '登录已过期，请重新登录');
      }
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('API请求失败:', error);
      return new APIResponse(false, null, error.message || '网络请求失败');
    }
  }

  // ==================== 管理员API ====================
  
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
    localStorage.removeItem('user_token');
    localStorage.removeItem('user_info');
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

  // 获取报单列表
  async getOrders(params = {}) {
    return await this.request('/admin/orders', {
      method: 'GET',
      params
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

  // 删除会员
  async deleteMember(id) {
    return await this.request(`/admin/members/${id}`, {
      method: 'DELETE'
    });
  }

  // 删除代理
  async deleteAgent(id) {
    return await this.request(`/admin/agents/${id}`, {
      method: 'DELETE'
    });
  }

  // 更换上级
  async changeParent(id, type, newParentId) {
    const endpoint = type === 'member' ? 'members' : 'agents';
    return await this.request(`/admin/${endpoint}/${id}/parent`, {
      method: 'PUT',
      body: { parentId: newParentId }
    });
  }

  // 代理充值
  async rechargeAgent(id, points, adminPassword) {
    return await this.request(`/admin/agents/${id}/recharge`, {
      method: 'POST',
      body: { points, adminPassword }
    });
  }

  // 获取代理下级
  async getAgentSubordinates(id, type) {
    return await this.request(`/admin/agents/${id}/subordinates`, {
      method: 'GET',
      params: { type }
    });
  }

  // 处理异常订单
  async processException(id) {
    return await this.request(`/admin/exceptions/${id}/process`, {
      method: 'PUT'
    });
  }

  // 导出报单
  async exportOrders(orderIds) {
    return await this.request('/admin/orders/export', {
      method: 'POST',
      body: { orderIds }
    });
  }

  // 修改用户支付密码
  async updatePayPassword(user, newPassword) {
    return await this.request('/admin/settings/pay-password', {
      method: 'PUT',
      body: { user, newPassword }
    });
  }

  // 创建数据备份
  async createBackup() {
    return await this.request('/admin/backup', {
      method: 'POST'
    });
  }

  // 获取备份列表
  async getBackupList() {
    return await this.request('/admin/backups');
  }

  // 恢复备份
  async restoreBackup(id) {
    return await this.request(`/admin/backups/${id}/restore`, {
      method: 'POST'
    });
  }

  // 删除备份
  async deleteBackup(id) {
    return await this.request(`/admin/backups/${id}`, {
      method: 'DELETE'
    });
  }

  // 发送通知
  async sendNotification(notificationData) {
    return await this.request('/admin/notifications', {
      method: 'POST',
      body: notificationData
    });
  }

  // 获取通知列表
  async getNotificationList() {
    return await this.request('/admin/notifications');
  }

  // ==================== 用户端API ====================

  // 用户注册
  async register(userData) {
    const response = await this.request('/user/register', {
      method: 'POST',
      body: userData
    });
    
    if (response.success && response.data) {
      this.token = response.data.token;
      this.userInfo = response.data.user;
      localStorage.setItem('user_token', this.token);
      localStorage.setItem('user_info', JSON.stringify(this.userInfo));
    }
    
    return response;
  }

  // 用户登录
  async userLogin(phone, password) {
    const response = await this.request('/user/login', {
      method: 'POST',
      body: { phone, password }
    });
    
    if (response.success && response.data) {
      this.token = response.data.token;
      this.userInfo = response.data.user;
      localStorage.setItem('user_token', this.token);
      localStorage.setItem('user_info', JSON.stringify(this.userInfo));
    }
    
    return response;
  }

  // 获取用户信息
  async getUserProfile() {
    return await this.request('/user/profile');
  }

  // 验证推广码唯一性
  async validatePromoCode(promoCode) {
    return await this.request('/user/validate-promo-code', {
      method: 'POST',
      body: { promoCode }
    });
  }

  // 创建报单
  async createOrder(orderData) {
    return await this.request('/orders', {
      method: 'POST',
      body: orderData
    });
  }

  // 获取订单列表
  async getUserOrders(params = {}) {
    return await this.request('/orders', {
      method: 'GET',
      params
    });
  }

  // 提交异常订单
  async submitExceptionOrder(orderId, description, imageFile) {
    const formData = new FormData();
    formData.append('orderId', orderId);
    formData.append('description', description);
    if (imageFile) {
      formData.append('image', imageFile);
    }
    
    return await this.request('/orders/exception', {
      method: 'POST',
      body: formData,
      headers: {
        // 不设置Content-Type，让浏览器自动设置（包含boundary）
      }
    });
  }

  // 获取非会员列表
  async getNonMembers() {
    return await this.request('/users/nonmembers');
  }

  // 添加非会员
  async addNonMember(nonMemberData) {
    return await this.request('/users/nonmembers', {
      method: 'POST',
      body: nonMemberData
    });
  }

  // 删除非会员
  async deleteNonMember(id) {
    return await this.request(`/users/nonmembers/${id}`, {
      method: 'DELETE'
    });
  }

  // 获取普通会员列表
  async getOrdinaryMembers() {
    return await this.request('/users/ordinary');
  }

  // 获取代理会员列表
  async getAgentMembers() {
    return await this.request('/users/agents');
  }

  // 升级为普通会员
  async upgradeToOrdinary(nonMemberId, phone) {
    return await this.request('/users/upgrade-to-ordinary', {
      method: 'POST',
      body: { nonMemberId, phone }
    });
  }

  // 升级为代理会员
  async upgradeToAgent(memberId) {
    return await this.request('/users/upgrade-to-agent', {
      method: 'POST',
      body: { memberId }
    });
  }

  // 获取金币余额
  async getPointsBalance() {
    return await this.request('/points/balance');
  }

  // 获取金币历史记录
  async getPointsHistory(params = {}) {
    return await this.request('/points/history', {
      method: 'GET',
      params
    });
  }

  // 转账金币
  async transferPoints(transferData) {
    return await this.request('/points/transfer', {
      method: 'POST',
      body: transferData
    });
  }

  // 获取奖励汇总
  async getRewardSummary() {
    return await this.request('/rewards/summary');
  }

  // 获取奖励明细
  async getRewardDetails(params = {}) {
    return await this.request('/rewards/details', {
      method: 'GET',
      params
    });
  }
}

// 创建全局API实例
const apiService = new APIService();

