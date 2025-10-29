"""
Template Engine - HTML template processing with Jinja2
Handles email template rendering and placeholder replacement
"""

from jinja2 import Template, Environment, TemplateError
from bs4 import BeautifulSoup
import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TemplateEngine:
    """Process HTML email templates"""
    
    def __init__(self):
        self.environment = Environment(autoescape=True)
        self.template = None
        self.raw_html = ""
    
    def load_from_file(self, file_path):
        """Load HTML template from file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.raw_html = f.read()
            
            logger.info(f"Template loaded from {file_path}")
            return True, "Template loaded successfully"
            
        except Exception as e:
            logger.error(f"Error loading template: {e}")
            return False, f"Error loading template: {str(e)}"
    
    def load_from_string(self, html_string):
        """Load HTML template from string"""
        try:
            self.raw_html = html_string
            logger.info("Template loaded from string")
            return True, "Template loaded successfully"
        except Exception as e:
            logger.error(f"Error loading template: {e}")
            return False, f"Error: {str(e)}"
    
    def extract_placeholders(self):
        """Extract all placeholders from template"""
        pattern = r'\{([a-zA-Z0-9_]+)\}'
        placeholders = list(set(re.findall(pattern, self.raw_html)))
        return placeholders
    
    def validate_template(self):
        """Validate HTML template structure"""
        try:
            soup = BeautifulSoup(self.raw_html, 'html.parser')
            
            validation_results = {
                'is_valid': True,
                'has_html_tag': soup.find('html') is not None,
                'has_body_tag': soup.find('body') is not None,
                'has_head_tag': soup.find('head') is not None,
                'placeholders': self.extract_placeholders(),
                'warnings': []
            }
            
            # Check for common issues
            if not validation_results['has_body_tag']:
                validation_results['warnings'].append("Template missing <body> tag")
            
            # Check for inline styles (good for email compatibility)
            style_tags = soup.find_all('style')
            if style_tags:
                validation_results['warnings'].append(
                    "Template contains <style> tags. Consider using inline styles for better email client compatibility."
                )
            
            return validation_results
            
        except Exception as e:
            logger.error(f"Error validating template: {e}")
            return {
                'is_valid': False,
                'error': str(e)
            }
    
    def render(self, data_dict):
        """Render template with data"""
        try:
            # Replace placeholders in raw HTML
            rendered = self.raw_html
            
            for key, value in data_dict.items():
                placeholder = f"{{{key}}}"
                rendered = rendered.replace(placeholder, str(value))
            
            return True, rendered
            
        except Exception as e:
            logger.error(f"Error rendering template: {e}")
            return False, f"Error rendering: {str(e)}"
    
    def preview_with_sample(self, sample_data):
        """Generate preview with sample data"""
        success, rendered = self.render(sample_data)
        
        if success:
            # Add preview notice
            preview_notice = """
            <div style="background: #fff3cd; border: 1px solid #ffc107; padding: 10px; text-align: center; font-family: Arial;">
                <strong>⚠️ PREVIEW MODE</strong> - This is how your email will look
            </div>
            """
            rendered = preview_notice + rendered
        
        return success, rendered
    
    def add_unsubscribe_link(self, unsubscribe_url):
        """Add unsubscribe link to template"""
        unsubscribe_html = f"""
        <div style="text-align: center; padding: 20px; color: #666; font-size: 12px;">
            <p>Don't want to receive these emails? 
            <a href="{unsubscribe_url}" style="color: #007bff;">Unsubscribe</a></p>
        </div>
        """
        
        # Try to add before closing body tag
        if '</body>' in self.raw_html:
            self.raw_html = self.raw_html.replace('</body>', unsubscribe_html + '</body>')
        else:
            self.raw_html += unsubscribe_html
    
    def optimize_for_email(self):
        """Optimize HTML for email clients"""
        try:
            soup = BeautifulSoup(self.raw_html, 'html.parser')
            
            # Remove script tags
            for script in soup.find_all('script'):
                script.decompose()
            
            # Convert external styles to inline (basic)
            # This is a simplified version
            
            self.raw_html = str(soup)
            logger.info("Template optimized for email")
            return True
            
        except Exception as e:
            logger.error(f"Error optimizing template: {e}")
            return False
    
    def get_plain_text_version(self):
        """Extract plain text version from HTML"""
        try:
            soup = BeautifulSoup(self.raw_html, 'html.parser')
            text = soup.get_text(separator='\n', strip=True)
            return text
        except Exception as e:
            logger.error(f"Error extracting plain text: {e}")
            return ""


class TemplateLibrary:
    """Built-in template library"""
    
    @staticmethod
    def get_professional_template():
        """Professional business email template"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f4f4f4;">
            <table width="100%" cellpadding="0" cellspacing="0" border="0">
                <tr>
                    <td align="center" style="padding: 20px;">
                        <table width="600" cellpadding="0" cellspacing="0" border="0" style="background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                            <!-- Header -->
                            <tr>
                                <td style="background-color: #007bff; padding: 30px; text-align: center;">
                                    <h1 style="color: #ffffff; margin: 0; font-size: 28px;">{company}</h1>
                                </td>
                            </tr>
                            <!-- Content -->
                            <tr>
                                <td style="padding: 40px 30px;">
                                    <h2 style="color: #333333; margin-top: 0;">Hello {name},</h2>
                                    <p style="color: #666666; line-height: 1.6; font-size: 16px;">
                                        Thank you for your interest in our services. We're excited to have you on board!
                                    </p>
                                    <p style="color: #666666; line-height: 1.6; font-size: 16px;">
                                        This email has been personalized for you at {email}.
                                    </p>
                                </td>
                            </tr>
                            <!-- Footer -->
                            <tr>
                                <td style="background-color: #f8f9fa; padding: 20px; text-align: center; color: #666666; font-size: 14px;">
                                    <p style="margin: 0;">&copy; 2025 {company}. All rights reserved.</p>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """
    
    @staticmethod
    def get_simple_template():
        """Simple email template"""
        return """
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2>Hello {name},</h2>
            <p>This is a personalized message for you.</p>
            <p>Your email: {email}</p>
            <p>Best regards,<br>{company}</p>
        </body>
        </html>
        """
    
    @staticmethod
    def get_marketing_template():
        """Marketing campaign template"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
        </head>
        <body style="margin: 0; padding: 0; background-color: #f5f5f5;">
            <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                    <td align="center" style="padding: 40px 0;">
                        <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                            <tr>
                                <td style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px; text-align: center;">
                                    <h1 style="color: #ffffff; margin: 0; font-size: 32px;">Special Offer</h1>
                                </td>
                            </tr>
                            <tr>
                                <td style="padding: 40px;">
                                    <h2 style="color: #333; margin-top: 0;">Hi {name}! 👋</h2>
                                    <p style="color: #666; font-size: 16px; line-height: 1.8;">
                                        We have an exclusive offer just for you at {company}!
                                    </p>
                                    <table width="100%" cellpadding="0" cellspacing="0" style="margin: 30px 0;">
                                        <tr>
                                            <td align="center">
                                                <a href="#" style="background-color: #667eea; color: #ffffff; padding: 15px 40px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">
                                                    Claim Your Offer
                                                </a>
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                            <tr>
                                <td style="background-color: #f9f9f9; padding: 20px; text-align: center; font-size: 12px; color: #999;">
                                    Sent to {email} | {company} &copy; 2025
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """
    
    @staticmethod
    def get_all_templates():
        """Get all available templates"""
        return {
            'Professional': TemplateLibrary.get_professional_template(),
            'Simple': TemplateLibrary.get_simple_template(),
            'Marketing': TemplateLibrary.get_marketing_template()
        }


# Test template engine
if __name__ == "__main__":
    engine = TemplateEngine()
    
    # Load professional template
    template_html = TemplateLibrary.get_professional_template()
    engine.load_from_string(template_html)
    
    # Extract placeholders
    placeholders = engine.extract_placeholders()
    print(f"Placeholders found: {placeholders}")
    
    # Validate template
    validation = engine.validate_template()
    print(f"Template valid: {validation}")
    
    # Render with sample data
    sample_data = {
        'name': 'John Doe',
        'email': 'john@example.com',
        'company': 'Acme Corp'
    }
    
    success, rendered = engine.render(sample_data)
    if success:
        print("Template rendered successfully!")
        print(rendered[:200] + "...")