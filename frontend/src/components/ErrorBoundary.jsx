import React, { Component } from 'react';
import { WarningCircle, ArrowClockwise } from '@phosphor-icons/react';

/**
 * React Error Boundary component.
 * Catches runtime JavaScript errors in child component trees, logs them,
 * and renders an institutional dark-mode fallback UI instead of crashing the app.
 */
export class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error(`[ErrorBoundary] Caught error in ${this.props.componentName || 'Component'}:`, error, errorInfo);
    this.setState({ errorInfo });
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  render() {
    if (this.state.hasError) {
      const componentName = this.props.componentName || 'This View';

      return (
        <div className="error-boundary-container" role="alert">
          <div className="error-boundary-card">
            <div className="error-boundary-header">
              <WarningCircle size={28} weight="fill" className="error-icon" />
              <div>
                <h3 className="error-title">{componentName} Encountered a Rendering Error</h3>
                <p className="error-subtitle">
                  The application isolated this issue to prevent crashing your session.
                </p>
              </div>
            </div>

            {this.state.error && (
              <div className="error-details font-mono">
                <p className="error-message">{this.state.error.toString()}</p>
                {this.state.errorInfo && (
                  <pre className="error-stack">{this.state.errorInfo.componentStack}</pre>
                )}
              </div>
            )}

            <div className="error-actions">
              <button
                type="button"
                className="btn btn-secondary error-retry-btn"
                onClick={this.handleReset}
              >
                <ArrowClockwise size={16} weight="bold" />
                Retry {componentName}
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
