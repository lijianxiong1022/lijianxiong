// 用户端API服务
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

const USER_API_BASE_URL = getApiBaseUrl();

class UserAPIService {
  constructor() {
    this.token = localStorage.getItem('user_token') || '';
    this.userInfo = JSON.parse(localStorage.getItem('user_info') || 'null');
  }

  // 通用请求方法
  async request(url, options = {}) {
    // 确保token是最新的
    this.token = localStorage.getItem('user_token') || '';
    
    const config = {
      method: options.method || 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      }
    };

    // 添加Authorization头
    if (this.token) {
      config.headers['Authorization'] = `Bearer ${this.token}`;
    }

    if (options.body) {
      config.body = typeof options.body === 'string' ? options.body : JSON.stringify(options.body);
    }

    // 调试日志
    console.log('API请求:', {
      url: `${USER_API_BASE_URL}${url}`,
      method: config.method,
      hasToken: !!this.token,
      tokenLength: this.token ? this.token.length : 0,
      tokenPreview: this.token ? this.token.substring(0, 20) + '...' : 'none',
      authorizationHeader: this.token ? `Bearer ${this.token.substring(0, 30)}...` : 'none',
      headers: Object.keys(config.headers)
    });

    try {
      const response = await fetch(`${USER_API_BASE_URL}${url}`, config);
      
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
        
        console.error('API请求失败:', {
          url: url,
          status: response.status,
          statusText: response.statusText,
          error: errorData,
          message: errorMessage
        });
        
        // 如果是401错误，检查是否是token问题
        if (response.status === 401) {
          // 只有在明确是token过期或无效时才清除token
          // 如果是"缺少Token"，可能是请求没有正确发送token，不清除
          if (errorMessage.includes('Token已过期') || errorMessage.includes('无效的Token') || errorMessage.includes('重新登录')) {
            console.warn('Token已过期或无效，清除token');
            this.logout();
            errorMessage = '登录已过期，请重新登录';
            // 不自动跳转，让调用方决定
          } else if (errorMessage.includes('缺少Token')) {
            // 缺少token，可能是请求配置问题，不清除已保存的token
            console.warn('请求缺少Token，但不清除已保存的token');
          }
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
      console.error('API请求错误:', error);
      // 检查是否是网络错误
      if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
        return {
          success: false,
          message: '网络连接失败，请检查后端服务是否运行',
          data: null
        };
      }
      return {
        success: false,
        message: error.message || '网络错误，请稍后重试',
        data: null
      };
    }
  }

  // 用户注册
  async register(data) {
    const response = await this.request('/user/register', {
      method: 'POST',
      body: {
        name: data.name,
        phone: data.phone,
        password: data.password,
        payPassword: data.payPassword,
        promoCode: data.promoCode || ''
      }
    });

    if (response.success && response.data) {
      this.token = response.data.token;
      this.userInfo = {
        userId: response.data.userId,
        promoCode: response.data.promoCode
      };
      localStorage.setItem('user_token', this.token);
      localStorage.setItem('user_info', JSON.stringify(this.userInfo));
    }

    return response;
  }

  // 用户登录
  async login(phone, password) {
    const response = await this.request('/user/login', {
      method: 'POST',
      body: {
        phone: phone,
        password: password
      }
    });

    if (response.success && response.data && response.data.token) {
      this.token = response.data.token;
      this.userInfo = response.data.user;
      localStorage.setItem('user_token', this.token);
      localStorage.setItem('user_info', JSON.stringify(this.userInfo));
      console.log('登录成功，Token已保存:', {
        tokenLength: this.token.length,
        userId: this.userInfo?.id
      });
    } else {
      console.error('登录失败:', response);
    }

    return response;
  }

  // 登出
  logout() {
    this.token = '';
    this.userInfo = null;
    localStorage.removeItem('user_token');
    localStorage.removeItem('user_info');
    // 不自动跳转，让调用方决定是否跳转
  }

  // 获取用户信息
  async getUserProfile() {
    return await this.request('/user/profile');
  }

  // 验证推广码
  async validatePromoCode(promoCode) {
    return await this.request('/user/validate-promo-code', {
      method: 'POST',
      body: { promoCode: promoCode }
    });
  }

  // 获取非会员列表
  async getNonMembers() {
    return await this.request('/users/nonmembers');
  }
  
  // 获取下级用户（普通会员和代理会员）
  async getSubordinates() {
    return await this.request('/users/subordinates');
  }

  // 添加非会员
  async addNonMember(name, link = '') {
    return await this.request('/users/nonmembers', {
      method: 'POST',
      body: {
        name: name,
        link: link
      }
    });
  }

  // 删除非会员
  async deleteNonMember(id) {
    return await this.request(`/users/nonmembers/${id}`, {
      method: 'DELETE'
    });
  }

  // 提交订单（报单）
  async submitOrder(nonMemberIds, settlementDate, quantity) {
    return await this.request('/orders', {
      method: 'POST',
      body: {
        nonMemberIds: nonMemberIds,
        settlementDate: settlementDate,
        quantity: quantity
      }
    });
  }

  // 获取订单列表
  async getOrders(params = {}) {
    const queryString = new URLSearchParams(params).toString();
    return await this.request(`/orders${queryString ? '?' + queryString : ''}`);
  }

  // 获取金币余额
  async getPointsBalance() {
    return await this.request('/points/balance');
  }

  // 获取交易记录列表
  async getTransactions(params = {}) {
    const queryString = new URLSearchParams(params).toString();
    return await this.request(`/transactions${queryString ? '?' + queryString : ''}`);
  }

  // 获取交易统计信息
  async getTransactionStatistics() {
    return await this.request('/transactions/statistics');
  }
  
  // 获取现金收益清单（代理用户）
  async getCashProfitList() {
    return await this.request('/transactions/cash-profit');
  }

  // 获取系统设置（用户端）
  async getSettings() {
    return await this.request('/user/settings');
  }
  
  // 转账金币
  async transferPoints(toPhone, quantity, unitPrice, payPassword, confirmedLowPrice = false) {
    return await this.request('/points/transfer', {
      method: 'POST',
      body: {
        toPhone: toPhone,
        quantity: quantity,
        unitPrice: unitPrice,
        payPassword: payPassword,
        confirmedLowPrice: confirmedLowPrice
      }
    });
  }

  // 获取订单统计信息
  async getOrderStatistics() {
    return await this.request('/orders/statistics');
  }

  // 获取奖励记录列表
  async getRewards(params = {}) {
    const queryString = new URLSearchParams(params).toString();
    return await this.request(`/rewards${queryString ? '?' + queryString : ''}`);
  }

  // 获取奖励统计信息
  async getRewardStatistics() {
    return await this.request('/rewards/statistics');
  }

  // 升级为代理
  async upgradeToAgent() {
    return await this.request('/users/upgrade-to-agent', {
      method: 'POST'
    });
  }

  // 检查是否已登录
  isAuthenticated() {
    // 从localStorage读取最新的token
    this.token = localStorage.getItem('user_token') || '';
    return !!this.token;
  }

  // 获取当前用户信息
  getCurrentUser() {
    return this.userInfo;
  }

  // 修改登录密码
  async changePassword(oldPassword, newPassword) {
    return await this.request('/user/change-password', {
      method: 'PUT',
      body: { oldPassword, newPassword }
    });
  }

  // 修改支付密码
  async changePayPassword(oldPassword, newPassword) {
    return await this.request('/user/change-pay-password', {
      method: 'PUT',
      body: { oldPassword, newPassword }
    });
  }

  // 提交异常订单
  async submitExceptionOrder(orderId, description, images) {
    const formData = new FormData();
    formData.append('orderId', orderId);
    formData.append('description', description);
    
    // 添加图片文件
    if (images && images.length > 0) {
      for (let i = 0; i < images.length; i++) {
        formData.append('images', images[i]);
      }
    }
    
    // 使用FormData时，不设置Content-Type，让浏览器自动设置
    const config = {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`
        // 不设置Content-Type，让浏览器自动设置multipart/form-data
      },
      body: formData
    };
    
    try {
      const response = await fetch(`${USER_API_BASE_URL}/exception-orders`, config);
      
      if (!response.ok) {
        const errorData = await response.json();
        return {
          success: false,
          message: errorData.message || '提交失败',
          data: null
        };
      }
      
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('提交异常订单失败:', error);
      return {
        success: false,
        message: error.message || '网络错误，请稍后重试',
        data: null
      };
    }
  }
}

// 创建全局实例
const userApiService = new UserAPIService();

