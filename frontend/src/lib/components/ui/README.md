# UI Components Library

This directory contains the complete Convergio UI Design System components built with SvelteKit and TypeScript.

## 📁 Directory Structure

```
src/lib/components/ui/
├── index.ts                    # Main exports
├── Button.svelte              # Primary button component
├── Input.svelte               # Form input component
├── Card.svelte                # Basic card component
├── StructuredCard.svelte      # Card with header/footer
├── Badge.svelte               # Status badges
├── Avatar.svelte              # User avatars
├── Switch.svelte              # Toggle switch
├── Checkbox.svelte            # Checkbox input
├── DashboardLayout.svelte     # Main layout
├── Header.svelte              # Navigation header
├── Sidebar.svelte             # Navigation sidebar
├── PageHeader.svelte          # Page title header
├── GridContainer.svelte       # Responsive grid
├── StatsCard.svelte           # Metrics display
├── ChartCard.svelte           # Chart container
├── Breadcrumbs.svelte         # Navigation breadcrumbs
├── QuickActions.svelte        # Floating actions
├── NotificationDropdown.svelte # Notifications
├── Modal.svelte               # Dialog modal
├── Tooltip.svelte             # Contextual tooltips
└── LoadingSpinner.svelte      # Loading indicators
```

## 🎯 Component Categories

### Core UI Components

Essential building blocks for user interfaces.

- **Button**: Action triggers with multiple variants
- **Input**: Form inputs with icons and validation
- **Card**: Content containers
- **Badge**: Status indicators
- **Avatar**: User representation
- **Switch**: Boolean toggle
- **Checkbox**: Selection input

### Dashboard Layout

Components for dashboard and application layouts.

- **DashboardLayout**: Main application layout
- **Header**: Top navigation bar
- **Sidebar**: Side navigation menu
- **PageHeader**: Page title and actions
- **GridContainer**: Responsive grid system

### Chart & Stats

Components for data visualization and metrics.

- **StatsCard**: Key performance indicators
- **ChartCard**: Chart container with controls

### Navigation

Components for application navigation.

- **Breadcrumbs**: Navigation trail
- **QuickActions**: Floating action button
- **NotificationDropdown**: Notification center

### Utilities

Helper components for common UI patterns.

- **Modal**: Dialog overlays
- **Tooltip**: Contextual help
- **LoadingSpinner**: Loading states

## 🚀 Quick Start

### Import Components

```typescript
import { Button, Input, Card, StatsCard } from "$lib/components/ui";
```

### Basic Usage

```svelte
<script>
  import { Button, Input, Card } from '$lib/components/ui';
  let inputValue = '';
</script>

<Card>
  <h2>Contact Form</h2>
  <Input bind:value={inputValue} placeholder="Enter your email" />
  <Button variant="primary">Submit</Button>
</Card>
```

## 📖 Component Documentation

### Button

Versatile button component with multiple variants and states.

#### Props

- `variant`: `'primary' | 'secondary' | 'outline' | 'ghost'`
- `size`: `'sm' | 'md' | 'lg' | 'icon'`
- `loading`: `boolean`
- `disabled`: `boolean`

#### Examples

```svelte
<!-- Basic button -->
<Button>Click me</Button>

<!-- Primary action -->
<Button variant="primary">Save Changes</Button>

<!-- Loading state -->
<Button loading>Saving...</Button>

<!-- Icon button -->
<Button size="icon" variant="outline">
  <Icon name="plus" />
</Button>
```

### Input

Form input with icons, validation states, and helper text.

#### Props

- `value`: `string`
- `placeholder`: `string`
- `variant`: `'default' | 'error' | 'success'`
- `size`: `'sm' | 'md' | 'lg'`
- `leadingIcon`: `string`
- `trailingIcon`: `string`
- `clearable`: `boolean`
- `disabled`: `boolean`
- `helperText`: `string`

#### Examples

```svelte
<!-- Basic input -->
<Input placeholder="Enter text" bind:value={text} />

<!-- With icon -->
<Input leadingIcon="search" placeholder="Search..." />

<!-- Error state -->
<Input variant="error" helperText="This field is required" />

<!-- Clearable input -->
<Input clearable bind:value={searchTerm} />
```

### StatsCard

Display key metrics with optional trend indicators.

#### Props

- `title`: `string`
- `value`: `string | number`
- `subtitle`: `string`
- `icon`: `string`
- `iconColor`: `'primary' | 'success' | 'warning' | 'error' | 'info' | 'gray'`
- `trend`: `TrendData`
- `variant`: `'default' | 'compact' | 'detailed'`
- `clickable`: `boolean`

#### Examples

```svelte
<!-- Basic stats card -->
<StatsCard
  title="Total Users"
  value={1234}
  icon="users"
  iconColor="primary"
/>

<!-- With trend data -->
<StatsCard
  title="Revenue"
  value="$45.2K"
  icon="currency"
  iconColor="success"
  trend={{
    percentage: 12.5,
    direction: 'up',
    period: 'last month'
  }}
/>
```

### Modal

Dialog component with backdrop and focus management.

#### Props

- `isOpen`: `boolean`
- `title`: `string`
- `size`: `'sm' | 'md' | 'lg' | 'xl' | 'full'`
- `persistent`: `boolean`
- `showCloseButton`: `boolean`

#### Examples

```svelte
<script>
  let showModal = false;
</script>

<Button on:click={() => showModal = true}>Open Modal</Button>

<Modal bind:isOpen={showModal} title="Confirm Action">
  <p>Are you sure you want to delete this item?</p>

  <svelte:fragment slot="footer">
    <Button variant="outline" on:click={() => showModal = false}>
      Cancel
    </Button>
    <Button variant="primary" on:click={handleDelete}>
      Delete
    </Button>
  </svelte:fragment>
</Modal>
```

### DashboardLayout

Main application layout with sidebar and header.

#### Props

- `sidebarCollapsed`: `boolean`

#### Examples

```svelte
<script>
  let sidebarCollapsed = false;
  let menuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: 'home' },
    { id: 'users', label: 'Users', icon: 'users' }
  ];
</script>

<DashboardLayout bind:sidebarCollapsed>
  <svelte:fragment slot="sidebar">
    <Sidebar {menuItems} collapsed={sidebarCollapsed} />
  </svelte:fragment>

  <svelte:fragment slot="header">
    <Header
      title="Dashboard"
      on:toggle-sidebar={() => sidebarCollapsed = !sidebarCollapsed}
    />
  </svelte:fragment>

  <!-- Main content -->
  <div class="p-6">
    <h1>Welcome to the Dashboard</h1>
  </div>
</DashboardLayout>
```

## 🎨 Theming

### CSS Custom Properties

All components use CSS custom properties for consistent theming:

```css
:root {
  /* Colors */
  --color-primary: theme("colors.primary.600");
  --color-surface: theme("colors.surface.white");

  /* Typography */
  --font-primary: "JetBrains Mono", monospace;
  --font-secondary: "Inter", sans-serif;

  /* Spacing */
  --space-unit: 0.25rem; /* 4px */

  /* Border radius */
  --radius-sm: 0.375rem;
  --radius-md: 0.5rem;
  --radius-lg: 0.75rem;
}
```

### Dark Mode

Components automatically support dark mode through CSS classes:

```html
<!-- Light mode -->
<html>
  <!-- Components use light theme -->
</html>

<!-- Dark mode -->
<html class="dark">
  <!-- Components automatically switch to dark theme -->
</html>
```

## ♿ Accessibility Features

### Keyboard Navigation

- All interactive elements support keyboard navigation
- Logical tab order throughout components
- Escape key closes modals and dropdowns

### Screen Reader Support

- Proper ARIA labels and roles
- Descriptive text for complex interactions
- Live regions for dynamic content updates

### Focus Management

- Visible focus indicators
- Focus trapping in modals
- Automatic focus return after closing

### Color Contrast

- WCAG AA compliant color combinations
- Sufficient contrast for all text
- Alternative indicators beyond color

## 🧪 Testing

### Component Testing

```bash
# Run component tests
npm run test:components

# Visual regression testing
npm run test:visual

# Accessibility testing
npm run test:a11y
```

### Manual Testing Checklist

- [ ] Keyboard navigation works
- [ ] Screen reader announces correctly
- [ ] Focus states are visible
- [ ] Colors have sufficient contrast
- [ ] Components work in light/dark mode
- [ ] Responsive behavior is correct
- [ ] Loading states display properly
- [ ] Error states are handled gracefully

## 🔧 Development Guidelines

### Component Structure

```svelte
<script lang="ts">
  // 1. Interface definition
  interface $$Props {
    // Define all props with proper types
  }

  // 2. Prop declarations with defaults
  export let prop: $$Props['prop'] = defaultValue;

  // 3. Component logic
  // 4. Event dispatchers
  // 5. Reactive statements
</script>

<!-- Template with proper accessibility -->
<div class="component-class" role="..." aria-label="...">
  <!-- Component content -->
</div>

<style>
  /* Component-specific styles */
  .component-class {
    /* Use design tokens */
    @apply bg-surface-white text-gray-900;
  }
</style>
```

### Best Practices

1. **TypeScript**: Always use proper TypeScript interfaces
2. **Accessibility**: Include ARIA labels and keyboard support
3. **Responsiveness**: Mobile-first design approach
4. **Performance**: Minimize bundle size and runtime overhead
5. **Testing**: Write tests for critical functionality
6. **Documentation**: Document props and usage examples

### Adding New Components

1. Create component file in `src/lib/components/ui/`
2. Define TypeScript interface for props
3. Implement component with accessibility features
4. Add to `index.ts` exports
5. Create usage examples
6. Write tests
7. Update documentation

## 📝 Contributing

### Code Style

- Use TypeScript for all components
- Follow Svelte style guidelines
- Use Tailwind CSS classes
- Include proper accessibility attributes
- Write descriptive comments

### Pull Request Process

1. Create feature branch from `main`
2. Implement component with tests
3. Update documentation
4. Test accessibility compliance
5. Submit pull request with description

## 🐛 Troubleshooting

### Common Issues

**Component not rendering**

- Check if component is properly imported
- Verify all required props are provided
- Check console for TypeScript errors

**Styling issues**

- Ensure Tailwind CSS is properly configured
- Check if design tokens are available
- Verify dark mode classes are applied

**Accessibility warnings**

- Add missing ARIA labels
- Ensure proper heading hierarchy
- Check color contrast ratios

### Getting Help

- Check existing component examples
- Review design system documentation
- Look at similar component implementations
- Ask in team chat or create an issue
