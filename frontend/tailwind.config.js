/** @type {import('tailwindcss').Config} */
export default {
	content: ['./src/**/*.{html,js,svelte,ts}'],
	darkMode: 'class',
	theme: {
		extend: {
			colors: {
				// Convergio brand colors (matching original)
				primary: {
					50: '#f0f9ff',
					100: '#e0f2fe',
					200: '#bae6fd',
					300: '#7dd3fc',
					400: '#38bdf8',
					500: '#0ea5e9',
					600: '#0284c7',
					700: '#0369a1',
					800: '#075985',
					900: '#0c4a6e',
					950: '#082f49'
				},
				gray: {
					50: '#f8fafc',
					100: '#f1f5f9',
					200: '#e2e8f0',
					300: '#cbd5e1',
					400: '#94a3b8',
					500: '#64748b',
					600: '#475569',
					700: '#334155',
					800: '#1e293b',
					900: '#0f172a',
					950: '#020617'
				},
				// Surface colors for dark mode
				surface: {
					0: '#000000',
					50: '#0f172a',
					100: '#1e293b',
					200: '#334155',
					300: '#475569',
					400: '#64748b',
					500: '#94a3b8',
					600: '#cbd5e1',
					700: '#e2e8f0',
					800: '#f1f5f9',
					900: '#f8fafc',
					950: '#ffffff'
				}
			},
			fontFamily: {
				sans: [
					'JetBrains Mono',
					'ui-monospace',
					'SFMono-Regular',
					'Monaco',
					'Consolas',
					'Liberation Mono',
					'Courier New',
					'monospace'
				],
				mono: [
					'JetBrains Mono',
					'Fira Code',
					'Monaco',
					'Consolas',
					'Liberation Mono',
					'Courier New',
					'monospace'
				]
			},
			fontSize: {
				'2xs': ['0.625rem', { lineHeight: '0.75rem' }],
			},
			spacing: {
				18: '4.5rem',
				88: '22rem',
				128: '32rem'
			},
			maxWidth: {
				'8xl': '88rem',
				'9xl': '96rem'
			},
			animation: {
				'fade-in': 'fadeIn 0.5s ease-in-out',
				'slide-in': 'slideIn 0.3s ease-out',
				'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
				'spin-slow': 'spin 3s linear infinite'
			},
			keyframes: {
				fadeIn: {
					'0%': { opacity: '0' },
					'100%': { opacity: '1' }
				},
				slideIn: {
					'0%': { transform: 'translateY(-10px)', opacity: '0' },
					'100%': { transform: 'translateY(0)', opacity: '1' }
				}
			},
			backdropBlur: {
				xs: '2px'
			},
			borderRadius: {
				'4xl': '2rem'
			}
		}
	},
	plugins: [
		// Custom CSS variables for theme switching
		function({ addBase, theme }) {
			addBase({
				':root': {
					'--font-sans': 'Inter, ui-sans-serif, system-ui, -apple-system, sans-serif',
					'--font-mono': 'ui-monospace, "SF Mono", Monaco, "Cascadia Code", monospace',
					'--color-primary': theme('colors.primary.600'),
					'--color-primary-hover': theme('colors.primary.700'),
					'--bg-primary': theme('colors.white'),
					'--bg-secondary': theme('colors.gray.50'),
					'--text-primary': theme('colors.gray.900'),
					'--text-secondary': theme('colors.gray.600'),
					'--border-color': theme('colors.gray.200')
				},
				'.dark': {
					'--color-primary': theme('colors.primary.400'),
					'--color-primary-hover': theme('colors.primary.300'),
					'--bg-primary': theme('colors.surface.50'),
					'--bg-secondary': theme('colors.surface.0'),
					'--text-primary': theme('colors.surface.900'),
					'--text-secondary': theme('colors.surface.600'),
					'--border-color': theme('colors.surface.200')
				}
			})
		}
	]
}