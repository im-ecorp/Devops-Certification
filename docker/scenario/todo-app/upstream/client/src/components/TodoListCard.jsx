import { useCallback, useEffect, useState } from 'react';
import { AddItemForm } from './AddNewItemForm';
import { ItemDisplay } from './ItemDisplay';

export function TodoListCard() {
    const [items, setItems] = useState(null);
    const [loadError, setLoadError] = useState(false);
    const [attempt, setAttempt] = useState(0);

    useEffect(() => {
        let active = true;
        fetch('/api/items')
            .then((response) => {
                if (response.ok === false) throw new Error('Request failed');
                return response.json();
            })
            .then((data) => {
                if (!Array.isArray(data)) throw new Error('Invalid items response');
                if (active) setItems(data);
            })
            .catch(() => { if (active) setLoadError(true); });
        return () => { active = false; };
    }, [attempt]);

    const retry = () => {
        setLoadError(false);
        setAttempt((current) => current + 1);
    };

    const onNewItem = useCallback((newItem) => {
        setItems((current) => [...current, newItem]);
    }, []);

    const onItemUpdate = useCallback((item) => {
        setItems((current) => current.map((existing) =>
            existing.id === item.id ? item : existing,
        ));
    }, []);

    const onItemRemoval = useCallback((item) => {
        setItems((current) => current.filter((existing) => existing.id !== item.id));
    }, []);

    if (loadError) return (
        <>
            <p role="alert">Could not load items. Please try again.</p>
            <button type="button" onClick={retry}>Retry</button>
        </>
    );
    if (items === null) return 'Loading...';

    return (
        <>
            <AddItemForm onNewItem={onNewItem} />
            {items.length === 0 && (
                <p className="text-center">No items yet! Add one above!</p>
            )}
            {items.map((item) => (
                <ItemDisplay
                    key={item.id}
                    item={item}
                    onItemUpdate={onItemUpdate}
                    onItemRemoval={onItemRemoval}
                />
            ))}
        </>
    );
}
