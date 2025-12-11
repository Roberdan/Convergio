<script lang="ts">
  import { onMount } from 'svelte';
  import { createEventDispatcher } from 'svelte';
  
  export let fields: FieldDefinition[] = [];
  export let values: Record<string, any> = {};
  export let readonly: boolean = false;
  export let showLabels: boolean = true;
  export let columns: number = 1;
  export let validationErrors: Record<string, string> = {};
  
  interface FieldDefinition {
    name: string;
    label: string;
    type: FieldType;
    required?: boolean;
    placeholder?: string;
    helpText?: string;
    options?: SelectOption[];
    validation?: ValidationRules;
    displayOrder?: number;
    defaultValue?: any;
    uiConfig?: UIConfig;
  }
  
  interface SelectOption {
    value: string;
    label: string;
    color?: string;
    icon?: string;
  }
  
  interface ValidationRules {
    min?: number;
    max?: number;
    minLength?: number;
    maxLength?: number;
  pattern?: string;
  // eslint-disable-next-line no-unused-vars
  custom?: Function | ((value: any) => string | null);
  }
  
  interface UIConfig {
    width?: 'full' | 'half' | 'third';
    rows?: number;
    showCharCount?: boolean;
    allowRichText?: boolean;
    dateFormat?: string;
    currencySymbol?: string;
  }
  
  type FieldType = 
    | 'text'
    | 'number'
    | 'date'
    | 'datetime'
    | 'select'
    | 'multiselect'
    | 'boolean'
    | 'url'
    | 'email'
    | 'phone'
    | 'currency'
    | 'percentage'
    | 'file'
    | 'user'
    | 'rich_text'
    | 'textarea';
  
  const dispatch = createEventDispatcher();
  
  let formData: Record<string, any> = { ...values };
  let errors: Record<string, string> = { ...validationErrors };
  let touched: Record<string, boolean> = {};
  
  onMount(() => {
    // Initialize default values
    fields.forEach(field => {
      if (!(field.name in formData) && field.defaultValue !== undefined) {
        formData[field.name] = field.defaultValue;
      }
    });
  });
  
  function handleChange(fieldName: string, value: any) {
    formData[fieldName] = value;
    touched[fieldName] = true;
    
    // Validate field
    const field = fields.find(f => f.name === fieldName);
    if (field) {
      const error = validateField(field, value);
      if (error) {
        errors[fieldName] = error;
      } else {
        delete errors[fieldName];
      }
    }
    
    // Emit change event
    dispatch('change', { field: fieldName, value, formData });
  }
  
  function handleBlur(fieldName: string) {
    touched[fieldName] = true;
    dispatch('blur', { field: fieldName, value: formData[fieldName] });
  }
  
  function validateField(field: FieldDefinition, value: any): string | null {
    // Required validation
    if (field.required && !value) {
      return `${field.label} is required`;
    }
    
    if (!field.validation) return null;
    
    const rules = field.validation;
    
    // Type-specific validations
    switch (field.type) {
      case 'text':
      case 'textarea':
      case 'rich_text':
        if (rules.minLength && value.length < rules.minLength) {
          return `${field.label} must be at least ${rules.minLength} characters`;
        }
        if (rules.maxLength && value.length > rules.maxLength) {
          return `${field.label} must be no more than ${rules.maxLength} characters`;
        }
  if (rules.pattern && !new RegExp(rules.pattern).test(value)) {
          return `${field.label} format is invalid`;
        }
        break;
        
      case 'number':
      case 'currency':
      case 'percentage': {
        const numValue = parseFloat(value);
        if (rules.min !== undefined && numValue < rules.min) {
          return `${field.label} must be at least ${rules.min}`;
        }
        if (rules.max !== undefined && numValue > rules.max) {
          return `${field.label} must be no more than ${rules.max}`;
        }
        break;
      }
        
      case 'email': {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(value)) {
          return `${field.label} must be a valid email address`;
        }
        break;
      }
        
      case 'url':
        try {
          new URL(value);
        } catch {
          return `${field.label} must be a valid URL`;
        }
        break;
        
      case 'phone': {
        const phoneRegex = new RegExp("^[\\d\\s\\-\\+\\(\\)]+$");
        if (!phoneRegex.test(value)) {
          return `${field.label} must be a valid phone number`;
        }
        break;
      }
    }
    
    // Custom validation
    if (rules.custom) {
      return rules.custom(value);
    }
    
    return null;
  }
  
  function getFieldWidth(field: FieldDefinition): string {
    const width = field.uiConfig?.width;
    if (columns === 1) return 'col-span-1';
    
    switch (width) {
      case 'half': return columns >= 2 ? 'col-span-1' : 'col-span-full';
      case 'third': return columns >= 3 ? 'col-span-1' : 'col-span-full';
      case 'full': 
      default: return 'col-span-full';
    }
  }
  
  // Removed unused helpers to satisfy lint
  
  // Sort fields by display order
  $: sortedFields = [...fields].sort((a, b) => 
    (a.displayOrder || 0) - (b.displayOrder || 0)
  );
  
  // Check if form is valid
  $: isValid = fields
    .filter(f => f.required)
    .every(f => formData[f.name]) && Object.keys(errors).length === 0;
  
  // Export validation function
  export function validate(): boolean {
    fields.forEach(field => {
      const error = validateField(field, formData[field.name]);
      if (error) {
        errors[field.name] = error;
      } else {
        delete errors[field.name];
      }
      touched[field.name] = true;
    });
    
    return isValid;
  }
  
  // Export form data getter
  export function getFormData(): Record<string, any> {
    return { ...formData };
  }
</script>

<div class="custom-form-renderer">
  <div class="grid grid-cols-{columns} gap-4">
    {#each sortedFields as field (field.name)}
      <div class="{getFieldWidth(field)} form-field">
        {#if showLabels}
          <label for={field.name} class="block text-sm font-medium text-surface-600 mb-1">
            {field.label}
            {#if field.required}
              <span class="text-red-500">*</span>
            {/if}
          </label>
        {/if}
        
        <!-- Text Input -->
        {#if field.type === 'text'}
          <input
            id={field.name}
            type="text"
            value={formData[field.name] || ''}
            on:input={(e) => handleChange(field.name, (e.target as HTMLInputElement).value)}
            on:blur={() => handleBlur(field.name)}
            placeholder={field.placeholder}
            disabled={readonly}
            class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500
                   {errors[field.name] ? 'border-red-500' : 'border-surface-300'}
                   {readonly ? 'bg-surface-100' : ''}"
          />
          {#if field.uiConfig?.showCharCount && field.validation?.maxLength}
            <div class="text-xs text-surface-500 mt-1">
              {formData[field.name]?.length || 0} / {field.validation.maxLength}
            </div>
          {/if}
        
        <!-- Number Input -->
        {:else if field.type === 'number'}
          <input
            id={field.name}
            type="number"
            value={formData[field.name] || ''}
            on:input={(e) => handleChange(field.name, parseFloat((e.target as HTMLInputElement).value))}
            on:blur={() => handleBlur(field.name)}
            min={field.validation?.min}
            max={field.validation?.max}
            placeholder={field.placeholder}
            disabled={readonly}
            class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500
                   {errors[field.name] ? 'border-red-500' : 'border-surface-300'}
                   {readonly ? 'bg-surface-100' : ''}"
          />
        
        <!-- Currency Input -->
        {:else if field.type === 'currency'}
          <div class="relative">
            <span class="absolute left-3 top-2 text-surface-500">
              {field.uiConfig?.currencySymbol || '$'}
            </span>
            <input
              id={field.name}
              type="number"
              step="0.01"
              value={formData[field.name] || ''}
              on:input={(e) => handleChange(field.name, parseFloat((e.target as HTMLInputElement).value))}
              on:blur={() => handleBlur(field.name)}
              min={field.validation?.min}
              max={field.validation?.max}
              placeholder={field.placeholder}
              disabled={readonly}
              class="w-full pl-8 pr-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500
                     {errors[field.name] ? 'border-red-500' : 'border-surface-300'}
                     {readonly ? 'bg-surface-100' : ''}"
            />
          </div>
        
        <!-- Percentage Input -->
        {:else if field.type === 'percentage'}
          <div class="relative">
            <input
              id={field.name}
              type="number"
              min="0"
              max="100"
              value={formData[field.name] || ''}
              on:input={(e) => handleChange(field.name, parseFloat((e.target as HTMLInputElement).value))}
              on:blur={() => handleBlur(field.name)}
              placeholder={field.placeholder}
              disabled={readonly}
              class="w-full pr-8 px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500
                     {errors[field.name] ? 'border-red-500' : 'border-surface-300'}
                     {readonly ? 'bg-surface-100' : ''}"
            />
            <span class="absolute right-3 top-2 text-surface-500">%</span>
          </div>
        
        <!-- Date Input -->
        {:else if field.type === 'date'}
          <input
            id={field.name}
            type="date"
            value={formData[field.name] || ''}
            on:input={(e) => handleChange(field.name, (e.target as HTMLInputElement).value)}
            on:blur={() => handleBlur(field.name)}
            disabled={readonly}
            class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500
                   {errors[field.name] ? 'border-red-500' : 'border-surface-300'}
                   {readonly ? 'bg-surface-100' : ''}"
          />
        
        <!-- DateTime Input -->
        {:else if field.type === 'datetime'}
          <input
            id={field.name}
            type="datetime-local"
            value={formData[field.name] || ''}
            on:input={(e) => handleChange(field.name, (e.target as HTMLInputElement).value)}
            on:blur={() => handleBlur(field.name)}
            disabled={readonly}
            class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500
                   {errors[field.name] ? 'border-red-500' : 'border-surface-300'}
                   {readonly ? 'bg-surface-100' : ''}"
          />
        
        <!-- Select Dropdown -->
        {:else if field.type === 'select'}
          <select
            id={field.name}
            value={formData[field.name] || ''}
            on:change={(e) => handleChange(field.name, (e.target as HTMLSelectElement).value)}
            on:blur={() => handleBlur(field.name)}
            disabled={readonly}
            class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500
                   {errors[field.name] ? 'border-red-500' : 'border-surface-300'}
                   {readonly ? 'bg-surface-100' : ''}"
          >
            <option value="">Select {field.label}</option>
            {#each field.options || [] as option}
              <option value={option.value}>
                {option.label}
              </option>
            {/each}
          </select>
        
        <!-- Multi-Select -->
        {:else if field.type === 'multiselect'}
          <div class="border rounded-lg p-2 {errors[field.name] ? 'border-red-500' : 'border-surface-300'}">
            {#each field.options || [] as option}
              <label class="flex items-center gap-2 py-1">
                <input
                  type="checkbox"
                  checked={(formData[field.name] || []).includes(option.value)}
                  on:change={(e) => {
                    const current = formData[field.name] || [];
                    const target = e.target as HTMLInputElement;
                    if (target.checked) {
                      handleChange(field.name, [...current, option.value]);
                    } else {
                      handleChange(field.name, current.filter((v: any) => v !== option.value));
                    }
                  }}
                  disabled={readonly}
                />
                <span class="text-sm">{option.label}</span>
              </label>
            {/each}
          </div>
        
        <!-- Boolean Checkbox -->
        {:else if field.type === 'boolean'}
          <label class="flex items-center gap-2">
            <input
              id={field.name}
              type="checkbox"
              checked={formData[field.name] || false}
              on:change={(e) => handleChange(field.name, (e.target as HTMLInputElement).checked)}
              disabled={readonly}
              class="w-4 h-4 text-blue-600 border-surface-300 rounded focus:ring-blue-500"
            />
            <span class="text-sm text-surface-600">{field.placeholder || field.label}</span>
          </label>
        
        <!-- Email Input -->
        {:else if field.type === 'email'}
          <input
            id={field.name}
            type="email"
            value={formData[field.name] || ''}
            on:input={(e) => handleChange(field.name, (e.target as HTMLInputElement).value)}
            on:blur={() => handleBlur(field.name)}
            placeholder={field.placeholder || 'email@example.com'}
            disabled={readonly}
            class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500
                   {errors[field.name] ? 'border-red-500' : 'border-surface-300'}
                   {readonly ? 'bg-surface-100' : ''}"
          />
        
        <!-- Phone Input -->
        {:else if field.type === 'phone'}
          <input
            id={field.name}
            type="tel"
            value={formData[field.name] || ''}
            on:input={(e) => handleChange(field.name, (e.target as HTMLInputElement).value)}
            on:blur={() => handleBlur(field.name)}
            placeholder={field.placeholder || '+1 (555) 000-0000'}
            disabled={readonly}
            class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500
                   {errors[field.name] ? 'border-red-500' : 'border-surface-300'}
                   {readonly ? 'bg-surface-100' : ''}"
          />
        
        <!-- URL Input -->
        {:else if field.type === 'url'}
          <input
            id={field.name}
            type="url"
            value={formData[field.name] || ''}
            on:input={(e) => handleChange(field.name, (e.target as HTMLInputElement).value)}
            on:blur={() => handleBlur(field.name)}
            placeholder={field.placeholder || 'https://example.com'}
            disabled={readonly}
            class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500
                   {errors[field.name] ? 'border-red-500' : 'border-surface-300'}
                   {readonly ? 'bg-surface-100' : ''}"
          />
        
        <!-- Textarea -->
        {:else if field.type === 'textarea'}
          <textarea
            id={field.name}
            value={formData[field.name] || ''}
            on:input={(e) => handleChange(field.name, (e.target as HTMLInputElement).value)}
            on:blur={() => handleBlur(field.name)}
            rows={field.uiConfig?.rows || 3}
            placeholder={field.placeholder}
            disabled={readonly}
            class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500
                   {errors[field.name] ? 'border-red-500' : 'border-surface-300'}
                   {readonly ? 'bg-surface-100' : ''}"
          ></textarea>
          {#if field.uiConfig?.showCharCount && field.validation?.maxLength}
            <div class="text-xs text-surface-500 mt-1">
              {formData[field.name]?.length || 0} / {field.validation.maxLength}
            </div>
          {/if}
        
        <!-- File Upload -->
        {:else if field.type === 'file'}
          <input
            id={field.name}
            type="file"
            on:change={(e) => handleChange(field.name, (e.target as HTMLInputElement).files?.[0])}
            disabled={readonly}
            class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500
                   {errors[field.name] ? 'border-red-500' : 'border-surface-300'}
                   {readonly ? 'bg-surface-100' : ''}"
          />
        {/if}
        
        <!-- Help Text -->
        {#if field.helpText}
          <p class="text-xs text-surface-500 mt-1">{field.helpText}</p>
        {/if}
        
        <!-- Error Message -->
        {#if errors[field.name] && touched[field.name]}
          <p class="text-xs text-red-500 mt-1">{errors[field.name]}</p>
        {/if}
      </div>
    {/each}
  </div>
</div>

<style>
  .form-field {
    margin-bottom: 1rem;
  }
  
  input:disabled,
  select:disabled,
  textarea:disabled {
    cursor: not-allowed;
    opacity: 0.6;
  }
</style>