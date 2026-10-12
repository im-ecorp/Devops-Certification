// @vitest-environment jsdom
import { afterEach, expect, test, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { AddItemForm } from './AddNewItemForm';

afterEach(() => { cleanup(); vi.unstubAllGlobals(); });

test('an HTTP error does not create an item and permits retry', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, json: async () => ({ error: 'unavailable' }) }));
    const onNewItem = vi.fn();
    render(<AddItemForm onNewItem={onNewItem} />);
    fireEvent.change(screen.getByLabelText('New item'), { target: { value: 'Keep this name' } });
    fireEvent.click(screen.getByText('Add Item'));
    await waitFor(() => expect(screen.getByText('Add Item')).toBeTruthy());
    expect(onNewItem).not.toHaveBeenCalled();
    expect(screen.getByLabelText('New item').value).toBe('Keep this name');
    expect(screen.getByRole('alert').textContent).toBe('Could not add item. Please try again.');
});

test('adds the successful response and clears the input', async () => {
    const item = { id: 'new', name: 'Task', completed: false };
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => item }));
    const onNewItem = vi.fn();
    render(<AddItemForm onNewItem={onNewItem} />);
    fireEvent.change(screen.getByLabelText('New item'), { target: { value: 'Task' } });
    fireEvent.click(screen.getByText('Add Item'));
    await waitFor(() => expect(onNewItem).toHaveBeenCalledWith(item));
    expect(screen.getByLabelText('New item').value).toBe('');
});
