export const bannerService = {
  async getHomeBanners() {
    try {
      // You'll need to create an endpoint for banners in your backend
      const response = await fetch('/api/banners?type=home_hero');
      if (!response.ok) throw new Error('Failed to fetch banners');
      return await response.json();
    } catch (error) {
      console.error('Error fetching banners:', error);
      // Return default banners
      return [
        {
          id: 1,
          title: 'Welcome to Pavitra Trading',
          description: 'Your trusted destination for quality products',
          image_url: '/static/img/banners/hero-banner-1.jpg',
          target_url: '/products'
        }
      ];
    }
  }
};