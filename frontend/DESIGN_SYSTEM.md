# Convergio UI Design System

A comprehensive design system built with SvelteKit, Tailwind CSS, and TypeScript, featuring a modern purple/violet theme and dashboard-focused components.

## 🎨 Design Tokens

### Color Palette

The design system is built around a purple/violet color palette with semantic variants:

**Primary (Purple/Violet)**

- `primary-50` to `primary-950` - Main brand colors
- Primary 600 (`#7c3aed`) as the main brand color

**Semantic Colors**

- **Success**: Green tones for positive actions
- **Warning**: Orange tones for warnings
- **Error**: Red tones for errors
- **Info**: Blue tones for information

**Surface Colors**

- Neutral grays from `surface-0` (white) to `surface-950` (near black)
- Semantic surface variants for borders and backgrounds

### Typography

**Font Family**

- Primary: `JetBrains Mono` (monospace for technical feel)
- Secondary: `Inter` (fallback system fonts)

**Font Sizes**

- `text-xs` (12px) to `text-4xl` (36px)
- Consistent 1.125 scale ratio

**Font Weights**

- `font-normal` (400)
- `font-medium` (500)
- `font-semibold` (600)
- `font-bold` (700)

### Spacing System

Consistent spacing scale using rem units:

- `space-1` (4px) to `space-16` (64px)
- Follows standard 4px baseline grid

### Border Radius

- `radius-sm` (6px) - Small elements
- `radius-md` (8px) - Default
- `radius-lg` (12px) - Cards
- `radius-xl` (16px) - Large elements
- `radius-2xl` (24px) - Very large elements
- `radius-full` - Circular elements

## 🧩 Component Library

### Core UI Components

#### Button

**Variants:** `primary`, `secondary`, `outline`, `ghost`
**Sizes:** `sm`, `md`, `lg`, `icon`
**States:** `loading`, `disabled`

```svelte
<Button variant="primary" size="md">Click me</Button>
<Button variant="outline" loading>Loading...</Button>
```

#### Input

**Features:** Icons, validation states, clearable
**Variants:** `default`, `error`, `success`
**Sizes:** `sm`, `md`, `lg`

```svelte
<Input placeholder="Enter text" leadingIcon="search" clearable />
<Input variant="error" helperText="This field is required" />
```

#### Card

**Variants:** `default`, `elevated`, `flat`
**Structure:** Header, content, footer slots

```svelte
<Card variant="elevated">
  <svelte:fragment slot="header">
    <h2>Card Title</h2>
  </svelte:fragment>
  Card content goes here
</Card>
```

#### Badge

**Variants:** `primary`, `secondary`, `success`, `warning`, `error`, `info`
**Sizes:** `sm`, `md`, `lg`

```svelte
<Badge variant="primary">New</Badge>
<Badge variant="success" size="sm">Online</Badge>
```

#### Avatar

**Variants:** Image, initials fallback
**Sizes:** `xs`, `sm`, `md`, `lg`, `xl`

```svelte
<Avatar src="/user.jpg" fallback="JD" size="md" />
```

### Dashboard Layout Components

#### DashboardLayout

Main layout container with sidebar and header integration.

```svelte
<DashboardLayout bind:sidebarCollapsed>
  <svelte:fragment slot="sidebar">
    <Sidebar {menuItems} />
  </svelte:fragment>
  <svelte:fragment slot="header">
    <Header title="Dashboard" />
  </svelte:fragment>
  <!-- Main content -->
</DashboardLayout>
```

#### Header

Navigation header with search, notifications, and user menu.

```svelte
<Header
  title="Dashboard"
  showSearch={true}
  showNotifications={true}
  notificationCount={5}
  userName="John Doe"
/>
```

#### Sidebar

Collapsible navigation sidebar with hierarchical menu support.

```svelte
<Sidebar
  {menuItems}
  collapsed={false}
  userInfo={{ name: "John", email: "john@example.com" }}
/>
```

### Chart and Stats Components

#### StatsCard

Displays key metrics with trend indicators.

**Variants:** `default`, `compact`, `detailed`

```svelte
<StatsCard
  title="Total Users"
  value={1234}
  icon="users"
  iconColor="primary"
  trend={{ percentage: 12.5, direction: 'up', period: 'last month' }}
/>
```

#### ChartCard

Container for charts with controls and legends.

```svelte
<ChartCard
  title="Revenue Overview"
  subtitle="Monthly revenue trends"
  fullscreenButton={true}
>
  <svelte:fragment slot="chart">
    <!-- Chart component -->
  </svelte:fragment>
  <svelte:fragment slot="legend">
    <!-- Legend items -->
  </svelte:fragment>
</ChartCard>
```

### Navigation Components

#### Breadcrumbs

Navigation breadcrumb trail.

```svelte
<Breadcrumbs
  items={[
    { label: 'Home', href: '/' },
    { label: 'Dashboard', href: '/dashboard' },
    { label: 'Analytics', active: true }
  ]}
/>
```

#### QuickActions

Floating action button with expandable actions.

```svelte
<QuickActions
  {actions}
  position="bottom-right"
  trigger="click"
  size="md"
/>
```

#### NotificationDropdown

Dropdown for displaying notifications.

```svelte
<NotificationDropdown
  {notifications}
  maxHeight="400px"
  showAvatar={true}
/>
```

### Utility Components

#### Modal

Dialog component with backdrop and focus management.

```svelte
<Modal
  bind:isOpen={showModal}
  title="Confirm Action"
  size="md"
  persistent={false}
>
  Modal content here
  <svelte:fragment slot="footer">
    <Button on:click={closeModal}>Cancel</Button>
    <Button variant="primary">Confirm</Button>
  </svelte:fragment>
</Modal>
```

#### Tooltip

Contextual help tooltips.

```svelte
<Tooltip text="This is a helpful tooltip" placement="top">
  <Button>Hover me</Button>
</Tooltip>
```

#### LoadingSpinner

Loading indicators with multiple variants.

**Variants:** `circle`, `dots`, `pulse`, `bars`
**Sizes:** `xs`, `sm`, `md`, `lg`, `xl`

```svelte
<LoadingSpinner variant="circle" size="md" text="Loading..." />
```

## 🎯 Usage Guidelines

### Design Principles

1. **Consistency**: Use design tokens consistently across all components
2. **Accessibility**: All components include proper ARIA labels and keyboard navigation
3. **Responsiveness**: Mobile-first approach with responsive breakpoints
4. **Performance**: Optimized for minimal bundle size and fast rendering

### Color Usage

- **Primary colors**: For primary actions, links, and focus states
- **Semantic colors**: Use appropriate colors for success, warning, error states
- **Neutral colors**: For text, borders, and backgrounds

### Typography Scale

- **Headers**: Use larger sizes (text-2xl to text-4xl) with semibold weight
- **Body text**: Use text-sm to text-base with normal weight
- **Captions**: Use text-xs for secondary information

### Spacing Guidelines

- **Component padding**: Use space-4 (16px) for default component padding
- **Section spacing**: Use space-8 (32px) between major sections
- **Element spacing**: Use space-2 to space-4 between related elements

## 🛠 Development

### Installation

```bash
npm install
```

### Development Server

```bash
npm run dev
```

### Build

```bash
npm run build
```

### Testing Components

Visit `/design-system-test` to see all components in action with various states and configurations.

## 📱 Responsive Design

The design system follows a mobile-first approach with these breakpoints:

- **Mobile**: < 640px
- **Tablet**: 640px - 1024px
- **Desktop**: > 1024px

All components are designed to work seamlessly across these breakpoints.

## ♿ Accessibility

### Features

- **Keyboard Navigation**: All interactive elements support keyboard navigation
- **Screen Reader Support**: Proper ARIA labels and roles
- **Focus Management**: Visible focus indicators and logical tab order
- **Color Contrast**: WCAG AA compliant color combinations
- **Reduced Motion**: Respects user's motion preferences

### Testing

- Test with keyboard navigation only
- Verify with screen readers
- Check color contrast ratios
- Test with motion preferences disabled

## 🔄 Future Enhancements

- [ ] Add animation presets
- [ ] Expand chart component library
- [ ] Add data table components
- [ ] Create form builder components
- [ ] Add theme switcher utilities
- [ ] Implement component composition patterns
