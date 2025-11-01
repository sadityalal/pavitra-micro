// Format currency with settings
export const formatCurrency = (amount, currency = 'INR', currencySymbol = '₹') => {
  if (!amount) return `${currencySymbol}0`;
  
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount).replace('₹', currencySymbol);
};

// Format product rating
export const formatRating = (rating) => {
  return rating?.toFixed(1) || '0.0';
};

// Generate product image URL - served from product service via nginx
export const getProductImageUrl = (imagePath) => {
  if (!imagePath || imagePath === 'null' || imagePath === 'undefined') {
    // Fallback to local asset if no image path
    return '/assets/img/product/product-1.webp';
  }
  
  if (imagePath.startsWith('http')) {
    // Already a full URL (external image)
    return imagePath;
  }
  
  if (imagePath.startsWith('/uploads/')) {
    // Backend image - served through nginx proxy
    // Remove any leading/trailing quotes or spaces
    const cleanPath = imagePath.replace(/^['"]|['"]$/g, '').trim();
    return cleanPath;
  }
  
  // Local asset image
  return `/assets/img/product/${imagePath}`;
};

// Get stock status badge class
export const getStockStatusBadge = (stockStatus) => {
  switch (stockStatus) {
    case 'in_stock':
      return { class: 'bg-success', text: 'In Stock' };
    case 'out_of_stock':
      return { class: 'bg-danger', text: 'Out of Stock' };
    case 'on_backorder':
      return { class: 'bg-warning', text: 'Backorder' };
    case 'pre_order':
      return { class: 'bg-info', text: 'Pre-Order' };
    default:
      return { class: 'bg-secondary', text: 'Unknown' };
  }
};

// Calculate savings
export const calculateSavings = (basePrice, salePrice) => {
  if (!basePrice || !salePrice || basePrice <= salePrice) return 0;
  return basePrice - salePrice;
};

// Format product specifications (JSON string from database)
export const formatSpecifications = (specs) => {
  if (!specs) return [];
  
  try {
    if (typeof specs === 'string') {
      return Object.entries(JSON.parse(specs)).map(([key, value]) => ({
        key: key.replace(/_/g, ' ').toUpperCase(),
        value
      }));
    }
    if (typeof specs === 'object') {
      return Object.entries(specs).map(([key, value]) => ({
        key: key.replace(/_/g, ' ').toUpperCase(),
        value
      }));
    }
  } catch (error) {
    console.error('Error parsing specifications:', error);
  }
  
  return [];
};

// Debounce function for search
export const debounce = (func, wait) => {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
};

// Get shipping info based on settings
export const getShippingInfo = (settings) => {
  if (!settings) return 'Free shipping available';
  
  return `Free shipping on orders over ${settings.currency_symbol}${settings.free_shipping_min_amount}`;
};

// Get return policy info
export const getReturnPolicy = (settings) => {
  if (!settings) return '30 days return policy';
  
  return `${settings.return_period_days} days return policy`;
};

// Check if running in Docker container
export const isDockerEnvironment = () => {
  return process.env.NODE_ENV === 'production';
};
