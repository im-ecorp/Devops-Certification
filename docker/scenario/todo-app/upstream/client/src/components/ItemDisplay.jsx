import { useState } from 'react';
import Container from 'react-bootstrap/Container';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import Button from 'react-bootstrap/Button';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faTrash } from '@fortawesome/free-solid-svg-icons/faTrash';
import { faSquare, faSquareCheck } from '@fortawesome/free-regular-svg-icons';
import './ItemDisplay.scss';

export function ItemDisplay({ item, onItemUpdate, onItemRemoval }) {
    const [error, setError] = useState('');
    const toggleCompletion = () => {
        setError('');
        fetch(`/api/items/${item.id}`, {
            method: 'PUT',
            body: JSON.stringify({
                name: item.name,
                completed: !item.completed,
            }),
            headers: { 'Content-Type': 'application/json' },
        })
            .then((r) => {
                if (!r.ok) throw new Error('Request failed');
                return r.json();
            })
            .then(onItemUpdate)
            .catch(() => setError('Could not update item. Please try again.'));
    };

    const removeItem = () => {
        setError('');
        fetch(`/api/items/${item.id}`, { method: 'DELETE' })
            .then((r) => {
                if (!r.ok) throw new Error('Request failed');
                onItemRemoval(item);
            })
            .catch(() => setError('Could not remove item. Please try again.'));
    };

    return (
        <Container fluid className={`item ${item.completed && 'completed'}`}>
            <Row>
                <Col xs={2} className="text-center">
                    <Button
                        className="toggles"
                        size="sm"
                        variant="link"
                        onClick={toggleCompletion}
                        aria-label={
                            item.completed
                                ? 'Mark item as incomplete'
                                : 'Mark item as complete'
                        }
                    >
                        <FontAwesomeIcon
                            icon={item.completed ? faSquareCheck : faSquare}
                        />
                    </Button>
                </Col>
                <Col xs={8} className="name">
                    {item.name}
                </Col>
                <Col xs={2} className="text-center remove">
                    <Button
                        size="sm"
                        variant="link"
                        onClick={removeItem}
                        aria-label="Remove Item"
                    >
                        <FontAwesomeIcon
                            icon={faTrash}
                            className="text-danger"
                        />
                    </Button>
                </Col>
            </Row>
            {error && <p role="alert">{error}</p>}
        </Container>
    );
}
