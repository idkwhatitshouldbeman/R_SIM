exports.handler = async (event, context) => {
  // Enable CORS
  const headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
  };

  // Handle preflight requests
  if (event.httpMethod === 'OPTIONS') {
    return {
      statusCode: 200,
      headers,
      body: '',
    };
  }

  try {
    const path = event.path;
    
    // Health check endpoint
    if (path === '/api/health' && event.httpMethod === 'GET') {
      return {
        statusCode: 200,
        headers: {
          ...headers,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          status: 'healthy',
          service: 'Netlify CFD Simulation Function',
          timestamp: Date.now(),
        }),
      };
    }

    // Simulation start endpoint
    if (path === '/api/simulation/start' && event.httpMethod === 'POST') {
      const data = JSON.parse(event.body || '{}');
      const simulationId = `sim_${Date.now()}`;
      
      return {
        statusCode: 200,
        headers: {
          ...headers,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          simulation_id: simulationId,
          status: 'started',
          message: 'Simulation started successfully',
        }),
      };
    }

    // Default response
    return {
      statusCode: 404,
      headers: {
        ...headers,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        error: 'Endpoint not found',
        path: path,
        method: event.httpMethod,
      }),
    };

  } catch (error) {
    return {
      statusCode: 500,
      headers: {
        ...headers,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        error: 'Internal server error',
        message: error.message,
      }),
    };
  }
};
