// src/QuoteGenerator.js

import React, { useEffect, useState } from 'react';
import axios from 'axios';

const QuoteGenerator = () => {
    const [text, setText] = useState('');
    const [speaker, setSpeaker] = useState('');
    const [loading, setLoading] = useState(true);

    const fetchQuote = async () => {
        setLoading(true);
        try {
            // Adding the endpoint for the EC2 instance on AWS (2024-12-17)
            const response = await axios.get('http://3.140.238.209:8000/random');
            console.log(response)
            setText(response.data.text);
            setSpeaker(response.data.speaker);
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
                        "{text}"
                    </blockquote>
                    <p>- {speaker}</p>
                    <button onClick={fetchQuote} class="btn">
                        Get Another Quote
                    </button>
                </div>
            )}
        </div>
    );
};

export default QuoteGenerator;