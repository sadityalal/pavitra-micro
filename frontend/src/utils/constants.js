export const SITE_NAME = process.env.REACT_APP_SITE_NAME || 'Pavitra Trading';

export const MEGA_MENU_CATEGORIES = {
  electronics: {
    name: 'Electronics',
    subcategories: ['Smartphones', 'Laptops', 'Audio Devices', 'Smart Home', 'Accessories']
  },
  clothing: {
    name: 'Clothing',
    subcategories: ["Men's Wear", "Women's Wear", "Kids Collection", 'Sportswear', 'Accessories']
  },
  home: {
    name: 'Home & Living',
    subcategories: ['Furniture', 'Decor', 'Kitchen', 'Bedding', 'Lighting']
  },
  beauty: {
    name: 'Beauty',
    subcategories: ['Skincare', 'Makeup', 'Haircare', 'Fragrances', 'Personal Care']
  }
};

export const CURRENCIES = [
  { code: 'USD', symbol: '$', name: 'US Dollar' },
  { code: 'EUR', symbol: '€', name: 'Euro' },
  { code: 'GBP', symbol: '£', name: 'British Pound' },
  { code: 'INR', symbol: '₹', name: 'Indian Rupee' }
];

export const LANGUAGES = [
  { code: 'en', name: 'English' },
  { code: 'es', name: 'Español' },
  { code: 'fr', name: 'Français' },
  { code: 'de', name: 'Deutsch' }
];
