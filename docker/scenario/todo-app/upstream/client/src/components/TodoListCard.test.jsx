// @vitest-environment jsdom
import { afterEach, expect, test, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { TodoListCard } from './TodoListCard';

vi.mock('./AddNewItemForm', () => ({ AddItemForm: ({ onNewItem }) => <button onClick={() => onNewItem({ id: 'new', name: 'new', completed: false })}>Add</button> }));
vi.mock('./ItemDisplay', () => ({ ItemDisplay: ({ item, onItemRemoval }) => <button onClick={() => onItemRemoval({ id: 'missing' })}>{item.name}</button> }));
afterEach(() => { cleanup(); vi.unstubAllGlobals(); });

test('ignores removal of an item absent from the list', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ json: async () => [{ id: 'first', name: 'first', completed: false }, { id: 'last', name: 'last', completed: false }] }));
    render(<TodoListCard />);
    await screen.findByText('first');
    fireEvent.click(screen.getByText('first'));
    expect(screen.getByText('first')).toBeTruthy();
});

test('shows an actionable error and retries when initial loading fails', async () => {
    const fetch = vi.fn()
        .mockRejectedValueOnce(new Error('network unavailable'))
        .mockResolvedValueOnce({ ok: true, json: async () => [] });
    vi.stubGlobal('fetch', fetch);
    render(<TodoListCard />);
    expect(await screen.findByRole('alert')).toHaveProperty('textContent', 'Could not load items. Please try again.');
    fireEvent.click(screen.getByRole('button', { name: 'Retry' }));
    expect(await screen.findByText('No items yet! Add one above!')).toBeTruthy();
    expect(fetch).toHaveBeenCalledTimes(2);
});

test('rejects a non-200 response without rendering an error as items', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 500, json: async () => ({ error: 'database down' }) }));
    render(<TodoListCard />);
    expect(await screen.findByRole('alert')).toHaveProperty('textContent', 'Could not load items. Please try again.');
});

test('rejects a non-array response without crashing', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => ({ error: 'bad response' }) }));
    render(<TodoListCard />);
    expect(await screen.findByRole('alert')).toHaveProperty('textContent', 'Could not load items. Please try again.');
});

test('adds an item after loading the list', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ json: async () => [] }));
    render(<TodoListCard />);
    await screen.findByText('No items yet! Add one above!');
    fireEvent.click(screen.getByText('Add'));
    await waitFor(() => expect(screen.getByText('new')).toBeTruthy());
});
