/**
 * 🔐 Convergio Client Hooks
 * Client-side security and error handling
 */

import type { HandleClientError } from '@sveltejs/kit';

export const handleError: HandleClientError = ({ error, event }) => {
	console.error('🔥 Client Error:', error);
	
	// Don't expose sensitive information in production
	if (import.meta.env.PROD) {
		return {
			message: 'An unexpected error occurred'
		};
	}

	return {
		message: error?.message || 'An unexpected error occurred'
	};
};