// @vitest-environment jsdom
import { afterEach, expect, test, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { ItemDisplay } from './ItemDisplay';

const item = { id: 'one', name: 'Task', completed: false };
afterEach(() => { cleanup(); vi.unstubAllGlobals(); });

test('an unsuccessful DELETE keeps the visible item', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false }));
    const onItemRemoval = vi.fn();
    render(<ItemDisplay item={item} onItemRemoval={onItemRemoval} />);
    fireEvent.click(screen.getByLabelText('Remove Item'));
    await screen.findByRole('alert');
    expect(onItemRemoval).not.toHaveBeenCalled();
});

test('updates completion using the successful response', async () => {
    const updated = { ...item, completed: true };
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => updated }));
    const onItemUpdate = vi.fn();
    render(<ItemDisplay item={item} onItemUpdate={onItemUpdate} />);
    fireEvent.click(screen.getByLabelText('Mark item as complete'));
    await waitFor(() => expect(onItemUpdate).toHaveBeenCalledWith(updated));
    expect(fetch).toHaveBeenCalledWith('/api/items/one', expect.objectContaining({ method: 'PUT' }));
});

test('removes an item only after a successful response', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true }));
    const onItemRemoval = vi.fn();
    render(<ItemDisplay item={{ ...item, completed: true }} onItemRemoval={onItemRemoval} />);
    expect(screen.getByLabelText('Mark item as incomplete')).toBeTruthy();
    fireEvent.click(screen.getByLabelText('Remove Item'));
    await waitFor(() => expect(onItemRemoval).toHaveBeenCalledWith(expect.objectContaining({ id: 'one' })));
});
