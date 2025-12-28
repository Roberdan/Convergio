<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	
	export let fields: FieldDefinition[] = [];
	export let values: Record<string, any> = {};
	export let errors: Record<string, string> = {};
	export let readonly = false;
	export let showLabels = true;
	export let columns = 1;
	
	const dispatch = createEventDispatcher();
	
	interface FieldDefinition {
		name: string;
		label: string;
		description?: string;
		field_type: string;
		is_required?: boolean;
		is_visible?: boolean;
		is_editable?: boolean;
		placeholder?: string;
		help_text?: string;
		validation_rules?: any;
		options?: Array<{value: string; label: string; color?: string}>;
		default_value?: any;
		group_name?: string;
		display_order?: number;
	}
	
	// Group fields by group_name
	$: groupedFields = fields.reduce((groups, field) => {
		const group = field.group_name || 'Default';
		if (!groups[group]) groups[group] = [];
		groups[group].push(field);
		return groups;
	}, {} as Record<string, FieldDefinition[]>);
	
	// Sort fields within groups by display_order
	$: Object.keys(groupedFields).forEach(group => {
		groupedFields[group].sort((a, b) => (a.display_order || 0) - (b.display_order || 0));
	});
	
	function handleChange(field: FieldDefinition, value: any) {
		values[field.name] = value;
		
		// Validate field
		const error = validateField(field, value);
		if (error) {
			errors[field.name] = error;
		} else {
			delete errors[field.name];
		}
		
		// Dispatch change event
		dispatch('change', { field: field.name, value, values });
	}
	
	function validateField(field: FieldDefinition, value: any): string | null {
		const rules = field.validation_rules || {};
		
		// Required validation
		if (field.is_required && !value) {
			return `${field.label} is required`;
		}
		
		// Type-specific validation
		switch (field.field_type) {
				case 'text':
				case 'rich_text': {
					if (rules.min_length && value.length < rules.min_length) {
						return `Minimum length is ${rules.min_length}`;
					}
					if (rules.max_length && value.length > rules.max_length) {
						return `Maximum length is ${rules.max_length}`;
					}
					if (rules.pattern) {
						const regex = new RegExp(rules.pattern);
						if (!regex.test(value)) {
							return rules.pattern_message || 'Invalid format';
						}
					}
					break;
				}
				case 'number':
				case 'currency':
				case 'percentage': {
					const numValue = parseFloat(value);
					if (isNaN(numValue)) {
						return 'Must be a number';
					}
					if (rules.min !== undefined && numValue < rules.min) {
						return `Minimum value is ${rules.min}`;
					}
					if (rules.max !== undefined && numValue > rules.max) {
						return `Maximum value is ${rules.max}`;
					}
					break;
				}
				case 'email': {
					const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
					if (!emailRegex.test(value)) {
						return 'Invalid email address';
					}
					break;
				}
				case 'url': {
					try {
						new URL(value);
					} catch {
						return 'Invalid URL';
					}
					break;
				}
				case 'phone': {
					const phoneRegex = /^[+]?[(]?[0-9]{1,4}[)]?[-\s.]?[(]?[0-9]{1,4}[)]?[-\s.]?[0-9]{1,9}$/;
					if (!phoneRegex.test(value)) {
						return 'Invalid phone number';
					}
					break;
				}
			}
		
		return null;
	}
	
	function getFieldComponent(field: FieldDefinition) {
		switch (field.field_type) {
			case 'text':
			case 'email':
			case 'url':
			case 'phone':
				return 'input';
			case 'number':
			case 'currency':
			case 'percentage':
				return 'number';
			case 'boolean':
				return 'checkbox';
			case 'date':
				return 'date';
			case 'datetime':
				return 'datetime-local';
			case 'select':
				return 'select';
			case 'multiselect':
				return 'multiselect';
			case 'rich_text':
				return 'textarea';
			case 'color':
				return 'color';
			case 'rating':
				return 'rating';
			case 'file':
				return 'file';
			default:
				return 'input';
		}
	}
	
	function getInputType(field: FieldDefinition): string {
		switch (field.field_type) {
			case 'email': return 'email';
			case 'url': return 'url';
			case 'phone': return 'tel';
			case 'number':
			case 'currency':
			case 'percentage':
				return 'number';
			default: return 'text';
		}
	}
	
	// removed unused helper
</script>

<div class="dynamic-form" style="--columns: {columns}">
	{#each Object.entries(groupedFields) as [groupName, groupFields]}
		{#if groupName !== 'Default'}
			<div class="field-group">
				<h3 class="group-title">{groupName}</h3>
			</div>
		{/if}
		
		<div class="fields-grid">
			{#each groupFields as field}
				{#if field.is_visible !== false}
					<div class="field-wrapper" class:full-width={field.field_type === 'rich_text'}>
						{#if showLabels}
							<label for={field.name} class="field-label">
								{field.label}
								{#if field.is_required}
									<span class="required">*</span>
								{/if}
							</label>
						{/if}
						
						{#if field.description}
							<p class="field-description">{field.description}</p>
						{/if}
						
						<div class="field-input">
							{#if getFieldComponent(field) === 'input'}
								<input
									id={field.name}
									type={getInputType(field)}
									value={values[field.name] || field.default_value || ''}
									placeholder={field.placeholder}
									disabled={readonly || field.is_editable === false}
									on:input={(e) => handleChange(field, e.currentTarget.value)}
									class="form-input"
									class:error={errors[field.name]}
								/>
								
							{:else if getFieldComponent(field) === 'number'}
								<div class="number-input">
									{#if field.field_type === 'currency'}
										<span class="prefix">$</span>
									{/if}
									<input
										id={field.name}
										type="number"
										value={values[field.name] || field.default_value || 0}
										placeholder={field.placeholder}
										disabled={readonly || field.is_editable === false}
										on:input={(e) => handleChange(field, parseFloat(e.currentTarget.value))}
										class="form-input"
										class:error={errors[field.name]}
										step={field.field_type === 'currency' ? '0.01' : '1'}
										min={field.validation_rules?.min}
										max={field.validation_rules?.max}
									/>
									{#if field.field_type === 'percentage'}
										<span class="suffix">%</span>
									{/if}
								</div>
								
							{:else if getFieldComponent(field) === 'checkbox'}
								<label class="checkbox-label">
									<input
										type="checkbox"
										checked={values[field.name] || field.default_value || false}
										disabled={readonly || field.is_editable === false}
										on:change={(e) => handleChange(field, e.currentTarget.checked)}
										class="form-checkbox"
									/>
									<span>{field.placeholder || 'Yes'}</span>
								</label>
								
							{:else if getFieldComponent(field) === 'date'}
								<input
									id={field.name}
									type="date"
									value={values[field.name] || field.default_value || ''}
									disabled={readonly || field.is_editable === false}
									on:change={(e) => handleChange(field, e.currentTarget.value)}
									class="form-input"
									class:error={errors[field.name]}
								/>
								
							{:else if getFieldComponent(field) === 'datetime-local'}
								<input
									id={field.name}
									type="datetime-local"
									value={values[field.name] || field.default_value || ''}
									disabled={readonly || field.is_editable === false}
									on:change={(e) => handleChange(field, e.currentTarget.value)}
									class="form-input"
									class:error={errors[field.name]}
								/>
								
							{:else if getFieldComponent(field) === 'select'}
								<select
									id={field.name}
									value={values[field.name] || field.default_value || ''}
									disabled={readonly || field.is_editable === false}
									on:change={(e) => handleChange(field, e.currentTarget.value)}
									class="form-select"
									class:error={errors[field.name]}
								>
									<option value="">Select...</option>
									{#each field.options || [] as option}
										<option value={option.value}>
											{option.label}
										</option>
									{/each}
								</select>
								
							{:else if getFieldComponent(field) === 'multiselect'}
								<div class="multiselect">
									{#each field.options || [] as option}
										<label class="checkbox-option">
											<input
												type="checkbox"
												value={option.value}
												checked={(values[field.name] || []).includes(option.value)}
												disabled={readonly || field.is_editable === false}
												on:change={(e) => {
													const current = values[field.name] || [];
													const newValue = e.currentTarget.checked
														? [...current, option.value]
														: current.filter((v: any) => v !== option.value);
													handleChange(field, newValue);
												}}
											/>
											<span
												class="option-label"
												style={option.color ? `background-color: ${option.color}20; border-color: ${option.color}` : ''}
											>
												{option.label}
											</span>
										</label>
									{/each}
								</div>
								
							{:else if getFieldComponent(field) === 'textarea'}
								<textarea
									id={field.name}
									value={values[field.name] || field.default_value || ''}
									placeholder={field.placeholder}
									disabled={readonly || field.is_editable === false}
									on:input={(e) => handleChange(field, e.currentTarget.value)}
									class="form-textarea"
									class:error={errors[field.name]}
									rows="4"
								></textarea>
								
							{:else if getFieldComponent(field) === 'color'}
								<input
									id={field.name}
									type="color"
									value={values[field.name] || field.default_value || '#000000'}
									disabled={readonly || field.is_editable === false}
									on:change={(e) => handleChange(field, e.currentTarget.value)}
									class="form-color"
								/>
								
							{:else if getFieldComponent(field) === 'rating'}
								<div class="rating-input">
									{#each [...Array(field.validation_rules?.max || 5).keys()] as i}
										<button
											type="button"
											class="rating-star"
											class:filled={i < (values[field.name] || 0)}
											disabled={readonly || field.is_editable === false}
											on:click={() => handleChange(field, i + 1)}
										>
											★
										</button>
									{/each}
								</div>
								
							{:else if getFieldComponent(field) === 'file'}
								<input
									id={field.name}
									type="file"
									disabled={readonly || field.is_editable === false}
									on:change={(e) => {
										const file = e.currentTarget.files?.[0];
										if (file) {
											handleChange(field, file);
										}
									}}
									class="form-file"
									accept={field.validation_rules?.accept}
								/>
							{/if}
						</div>
						
						{#if field.help_text}
							<p class="field-help">{field.help_text}</p>
						{/if}
						
						{#if errors[field.name]}
							<p class="field-error">{errors[field.name]}</p>
						{/if}
					</div>
				{/if}
			{/each}
		</div>
	{/each}
</div>

<style>
	.dynamic-form {
		width: 100%;
	}
	
	.field-group {
		margin-bottom: 1.5rem;
	}
	
	.group-title {
		font-size: 1.125rem;
		font-weight: 600;
		color: #374151;
		margin-bottom: 1rem;
		padding-bottom: 0.5rem;
		border-bottom: 1px solid #e5e7eb;
	}
	
	.fields-grid {
		display: grid;
		grid-template-columns: repeat(var(--columns, 1), 1fr);
		gap: 1.5rem;
		margin-bottom: 1.5rem;
	}
	
	.field-wrapper {
		display: flex;
		flex-direction: column;
	}
	
	.field-wrapper.full-width {
		grid-column: 1 / -1;
	}
	
	.field-label {
		font-weight: 500;
		color: #374151;
		margin-bottom: 0.25rem;
		font-size: 0.875rem;
	}
	
	.required {
		color: #ef4444;
		margin-left: 0.25rem;
	}
	
	.field-description {
		font-size: 0.75rem;
		color: #6b7280;
		margin-bottom: 0.5rem;
	}
	
	.field-input {
		position: relative;
	}
	
	.form-input, .form-select, .form-textarea {
		width: 100%;
		padding: 0.5rem 0.75rem;
		border: 1px solid #d1d5db;
		border-radius: 6px;
		font-size: 0.875rem;
		transition: all 0.2s;
	}
	
	.form-input:focus, .form-select:focus, .form-textarea:focus {
		outline: none;
		border-color: #3b82f6;
		box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
	}
	
	.form-input.error, .form-select.error, .form-textarea.error {
		border-color: #ef4444;
	}
	
	.form-input:disabled, .form-select:disabled, .form-textarea:disabled {
		background-color: #f3f4f6;
		cursor: not-allowed;
	}
	
	.number-input {
		display: flex;
		align-items: center;
	}
	
	.prefix, .suffix {
		padding: 0.5rem;
		color: #6b7280;
		background: #f3f4f6;
		border: 1px solid #d1d5db;
		font-size: 0.875rem;
	}
	
	.prefix {
		border-right: none;
		border-radius: 6px 0 0 6px;
	}
	
	.suffix {
		border-left: none;
		border-radius: 0 6px 6px 0;
	}
	
	.number-input .form-input {
		border-radius: 0;
		flex: 1;
	}
	
	.number-input .prefix + .form-input {
		border-radius: 0 6px 6px 0;
	}
	
	.number-input .form-input:has(+ .suffix) {
		border-radius: 6px 0 0 6px;
	}
	
	.checkbox-label {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		cursor: pointer;
	}
	
	.form-checkbox {
		width: 1rem;
		height: 1rem;
	}
	
	.multiselect {
		display: flex;
		flex-wrap: wrap;
		gap: 0.5rem;
	}
	
	.checkbox-option {
		display: flex;
		align-items: center;
		gap: 0.25rem;
		cursor: pointer;
	}
	
	.option-label {
		padding: 0.25rem 0.5rem;
		border: 1px solid #e5e7eb;
		border-radius: 4px;
		font-size: 0.875rem;
	}
	
	.form-color {
		width: 3rem;
		height: 2.5rem;
		border: 1px solid #d1d5db;
		border-radius: 6px;
		cursor: pointer;
	}
	
	.rating-input {
		display: flex;
		gap: 0.25rem;
	}
	
	.rating-star {
		background: none;
		border: none;
		font-size: 1.5rem;
		color: #d1d5db;
		cursor: pointer;
		transition: color 0.2s;
	}
	
	.rating-star.filled {
		color: #fbbf24;
	}
	
	.rating-star:hover {
		color: #f59e0b;
	}
	
	.rating-star:disabled {
		cursor: not-allowed;
		opacity: 0.5;
	}
	
	.form-file {
		width: 100%;
		padding: 0.5rem;
		border: 1px solid #d1d5db;
		border-radius: 6px;
		font-size: 0.875rem;
		background: white;
	}
	
	.field-help {
		font-size: 0.75rem;
		color: #6b7280;
		margin-top: 0.25rem;
	}
	
	.field-error {
		font-size: 0.75rem;
		color: #ef4444;
		margin-top: 0.25rem;
	}
	
	@media (max-width: 768px) {
		.fields-grid {
			grid-template-columns: 1fr;
		}
	}
</style>