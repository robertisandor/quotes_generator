// src/QuoteGenerator.js

import React, { useEffect, useState } from 'react';
import axios from 'axios';

const QuoteGenerator = () => {
    const [quote, setQuote] = useState('');
    const [author, setAuthor] = useState('');
    const [loading, setLoading] = useState(true);

    const fetchQuote = async () => {
        setLoading(true);
        try {
            const response = await axios.get('https://api.quotable.io/random');
            setQuote(response.data.content);
            setAuthor(response.data.author);
        } catch (error) {
            console.error('Error fetching quote:', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchQuote();
    }, []);

    return (
        <div>
            {loading ? (
                <p>Loading...</p>
            ) : (
                <div>
                    <blockquote>
                        "{quote}"
                    </blockquote>
                    <p>- {author}</p>
                    <button onClick={fetchQuote} class="btn">
                        Get Another Quote
                    </button>
                </div>
            )}
        </div>
    );
};

export default QuoteGenerator;