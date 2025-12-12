/**
 * Pagination Handler Utility
 * Manages pagination state for API requests with offset and cursor-based pagination
 */

import { PaginationState } from '../types/index.js';

export class PaginationHandler {
  private states: Map<string, PaginationState> = new Map();

  createState(key: string, limit: number = 20): PaginationState {
    const state: PaginationState = {
      offset: 0,
      limit,
      hasMore: true,
    };
    this.states.set(key, state);
    return state;
  }

  getState(key: string): PaginationState | undefined {
    return this.states.get(key);
  }

  updateState(key: string, updates: Partial<PaginationState>): void {
    const state = this.states.get(key);
    if (state) {
      Object.assign(state, updates);
    }
  }

  nextPage(key: string): PaginationState | undefined {
    const state = this.states.get(key);
    if (!state || !state.hasMore) {
      return undefined;
    }

    state.offset += state.limit;
    return state;
  }

  resetState(key: string): void {
    const state = this.states.get(key);
    if (state) {
      state.offset = 0;
      state.hasMore = true;
    }
  }

  clearState(key: string): void {
    this.states.delete(key);
  }

  calculateHasMore(total: number, offset: number, limit: number): boolean {
    return offset + limit < total;
  }
}

export const paginationHandler = new PaginationHandler();
