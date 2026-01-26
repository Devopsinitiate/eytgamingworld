"""
Unit tests for Task 5.4: Enhanced Master Index and Navigation Generation.

This module tests the enhanced master index generation functionality
implemented in the StructureGenerator class.
"""

import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import sys
import os
sys.path.append(os.path.dirname(__file__))

from generator import StructureGenerator
from models import (
    DocumentationStructure, FileAnalysis, ConsolidationGroup,
    Category, ContentType, ContentMetadata, Priority, IndexConfig
)
from config import ConsolidationConfig


class TestEnhancedMasterIndexGeneration:
    """Test enhanced master index generation functionality."""
    
    @pytest.fixture
    def generator(self):
        """Create a StructureGenerator instance for testing."""
        config = ConsolidationConfig()
        return StructureGenerator(config)
    
    @pytest.fixture
    def sample_structure(self):
        """Create a sample DocumentationStructure for testing."""
        return DocumentationStructure()
    
    @pytest.fixture
    def sample_file_analyses(self):
        """Create sample file analyses for testing."""
        return [
            FileAnalysis(
                filepath=Path('PAYMENT_SETUP.md'),
                filename='PAYMENT_SETUP.md',
                category=Category.FEATURE_DOCS,
                content_type=ContentType.FEATURE_GUIDE,
                metadata=ContentMetadata(
                    word_count=1200,
                    key_topics=['payment', 'setup', 'configuration'],
                    last_modified=datetime(2024, 1, 15),
                    internal_links=['config.md', 'api.md']
                )
            ),
            FileAnalysis(
                filepath=Path('TOURNAMENT_GUIDE.md'),
                filename='TOURNAMENT_GUIDE.md',
                category=Category.FEATURE_DOCS,
                content_type=ContentType.FEATURE_GUIDE,
                metadata=ContentMetadata(
                    word_count=2500,
                    key_topics=['tournament', 'management', 'competition'],
                    last_modified=datetime(2024, 1, 20)
                )
            ),
            FileAnalysis(
                filepath=Path('TASK_5_1_COMPLETE.md'),
                filename='TASK_5_1_COMPLETE.md',
                category=Category.IMPLEMENTATION_COMPLETION,
                content_type=ContentType.COMPLETION_SUMMARY,
                metadata=ContentMetadata(
                    word_count=800,
                    key_topics=['implementation', 'task', 'completion'],
                    last_modified=datetime(2024, 1, 10)
                )
            ),
            FileAnalysis(
                filepath=Path('QUICK_SETUP_GUIDE.md'),
                filename='QUICK_SETUP_GUIDE.md',
                category=Category.QUICK_REFERENCES,
                content_type=ContentType.QUICK_REFERENCE,
                metadata=ContentMetadata(
                    word_count=600,
                    key_topics=['quick', 'setup', 'guide'],
                    last_modified=datetime(2024, 1, 25)
                )
            ),
            FileAnalysis(
                filepath=Path('test_results.md'),
                filename='test_results.md',
                category=Category.TESTING_VALIDATION,
                content_type=ContentType.TEST_REPORT,
                metadata=ContentMetadata(
                    word_count=1500,
                    key_topics=['testing', 'validation', 'results'],
                    last_modified=datetime(2024, 1, 18)
                )
            )
        ]
    
    @pytest.fixture
    def sample_consolidated_groups(self):
        """Create sample consolidation groups for testing."""
        return [
            ConsolidationGroup(
                group_id='payment_docs',
                category=Category.FEATURE_DOCS,
                primary_file='PAYMENT_SETUP.md',
                related_files=['PAYMENT_CONFIG.md', 'PAYMENT_API.md'],
                output_filename='payment_comprehensive_guide.md'
            ),
            ConsolidationGroup(
                group_id='implementation_summary',
                category=Category.IMPLEMENTATION_COMPLETION,
                primary_file='TASK_5_1_COMPLETE.md',
                related_files=['TASK_5_2_COMPLETE.md', 'TASK_5_3_COMPLETE.md'],
                output_filename='implementation_summary.md'
            )
        ]
    
    def test_generate_master_index_basic_structure(self, generator, sample_structure, 
                                                  sample_file_analyses, sample_consolidated_groups):
        """Test that master index has basic required structure."""
        index_content = generator.generate_master_index(
            sample_structure, sample_file_analyses, sample_consolidated_groups
        )
        
        # Check basic structure elements
        assert "# Documentation Index" in index_content
        assert "## 🚀 Quick Start Guide" in index_content
        assert "## 📚 Documentation Catalog" in index_content
        assert "## 🔍 Navigation & Search Guide" in index_content
        assert "## 📊 Project Documentation Overview" in index_content
        assert "## 📅 Recent Documentation Updates" in index_content
        assert "## 🛠️ Developer Resources" in index_content
        assert "## 🔧 Documentation Maintenance" in index_content
        
        # Check for badges and enhanced formatting
        assert "[![Documentation Status]" in index_content
        assert "[![Django]" in index_content
        
        # Check for emojis and enhanced formatting
        assert "🚀" in index_content
        assert "📚" in index_content
        assert "🔍" in index_content
    
    def test_enhanced_header_generation(self, generator, sample_structure):
        """Test enhanced header generation."""
        header = generator._generate_enhanced_header(sample_structure)
        
        # Check header content
        header_text = "\n".join(header)
        assert "# Documentation Index" in header_text
        assert "[![Documentation Status]" in header_text
        assert "[![Django]" in header_text
        assert "🚀 **Quick Navigation:**" in header_text
        assert "📚 **Comprehensive Coverage:**" in header_text
        assert "🔍 **Search-Friendly:**" in header_text
        assert "⚡ **Developer-Focused:**" in header_text
    
    def test_enhanced_quick_start_section(self, generator, sample_structure):
        """Test enhanced quick start section generation."""
        quick_start = generator._generate_enhanced_quick_start_section(sample_structure)
        
        quick_start_text = "\n".join(quick_start)
        
        # Check for enhanced structure
        assert "## 🚀 Quick Start Guide" in quick_start_text
        assert "### New to the Project?" in quick_start_text
        assert "### Experienced Developer?" in quick_start_text
        assert "### Common Developer Tasks" in quick_start_text
        
        # Check for table format
        assert "| Task | Documentation | Quick Link |" in quick_start_text
        assert "|------|---------------|------------|" in quick_start_text
        
        # Check for specific links
        assert "[setup/installation.md]" in quick_start_text
        assert "[features/payments/]" in quick_start_text
        assert "[features/tournaments/]" in quick_start_text
    
    def test_enhanced_table_of_contents(self, generator, sample_structure, 
                                       sample_file_analyses, sample_consolidated_groups):
        """Test enhanced table of contents generation."""
        toc = generator._generate_enhanced_table_of_contents(
            sample_structure, sample_file_analyses, sample_consolidated_groups
        )
        
        toc_text = "\n".join(toc)
        
        # Check for enhanced structure
        assert "## 📚 Documentation Catalog" in toc_text
        assert "### By Category" in toc_text
        
        # Check for category icons and descriptions
        assert "🎯" in toc_text  # Feature docs icon
        assert "📊" in toc_text  # Implementation completion icon
        assert "🔍" in toc_text  # Quick references icon
        
        # Check for enhanced descriptions
        assert "Feature-specific documentation" in toc_text
        assert "Implementation history" in toc_text
    
    def test_enhanced_search_tips_section(self, generator, sample_structure):
        """Test enhanced search tips section generation."""
        search_tips = generator._generate_enhanced_search_tips_section(sample_structure)
        
        search_tips_text = "\n".join(search_tips)
        
        # Check for enhanced structure
        assert "## 🔍 Navigation & Search Guide" in search_tips_text
        assert "### Finding What You Need" in search_tips_text
        assert "### Search Strategies" in search_tips_text
        
        # Check for specific search guidance
        assert "**By Purpose:**" in search_tips_text
        assert "**By File Type:**" in search_tips_text
        assert "**IDE/Editor Search:**" in search_tips_text
        assert "**Command Line:**" in search_tips_text
        
        # Check for code examples
        assert "```bash" in search_tips_text
        assert "grep -r" in search_tips_text
        assert "find docs/" in search_tips_text
    
    def test_enhanced_project_overview_section(self, generator, sample_file_analyses, 
                                              sample_consolidated_groups):
        """Test enhanced project overview section generation."""
        overview = generator._generate_enhanced_project_overview_section(
            sample_file_analyses, sample_consolidated_groups
        )
        
        overview_text = "\n".join(overview)
        
        # Check for enhanced structure
        assert "## 📊 Project Documentation Overview" in overview_text
        assert "### Documentation Statistics" in overview_text
        assert "### Content Breakdown by Category" in overview_text
        assert "### Key Features Documented" in overview_text
        assert "### Documentation Quality Metrics" in overview_text
        
        # Check for statistics
        assert "**📄 Total Documents:**" in overview_text
        assert "**📝 Total Word Count:**" in overview_text
        assert "**🔗 Consolidated Groups:**" in overview_text
        assert "**📁 Categories Covered:**" in overview_text
    
    def test_enhanced_recent_updates_section(self, generator, sample_file_analyses):
        """Test enhanced recent updates section generation."""
        updates = generator._generate_enhanced_recent_updates_section(sample_file_analyses)
        
        updates_text = "\n".join(updates)
        
        # Check for enhanced structure
        assert "## 📅 Recent Documentation Updates" in updates_text
        assert "### Latest Changes" in updates_text
        assert "### Update Frequency" in updates_text
        
        # Check for table format
        assert "| Document | Category | Updated | Size |" in updates_text
        assert "|----------|----------|---------|------|" in updates_text
        
        # Check for specific file information
        assert "Feature Docs" in updates_text  # Category name formatting
        assert "2024-01-25" in updates_text  # Most recent date
    
    def test_developer_resources_section(self, generator, sample_structure):
        """Test developer resources section generation."""
        resources = generator._generate_developer_resources_section(sample_structure)
        
        resources_text = "\n".join(resources)
        
        # Check for structure
        assert "## 🛠️ Developer Resources" in resources_text
        assert "### Essential Tools & Links" in resources_text
        assert "### Getting Help" in resources_text
        
        # Check for specific resources
        assert "**Development Environment:**" in resources_text
        assert "**Project-Specific Resources:**" in resources_text
        assert "Django Documentation" in resources_text
        assert "pytest Documentation" in resources_text
    
    def test_maintenance_section(self, generator, sample_structure):
        """Test maintenance section generation."""
        maintenance = generator._generate_maintenance_section(sample_structure)
        
        maintenance_text = "\n".join(maintenance)
        
        # Check for structure
        assert "## 🔧 Documentation Maintenance" in maintenance_text
        assert "### About This Documentation" in maintenance_text
        assert "### Maintenance Guidelines" in maintenance_text
        
        # Check for specific content
        assert "Documentation Consolidation System" in maintenance_text
        assert "**Adding New Documentation:**" in maintenance_text
        assert "**Updating Existing Documentation:**" in maintenance_text
    
    def test_enhanced_footer(self, generator):
        """Test enhanced footer generation."""
        footer = generator._generate_enhanced_footer()
        
        footer_text = "\n".join(footer)
        
        # Check for structure
        assert "## 📋 Documentation Metadata" in footer_text
        assert "### Quick Links" in footer_text
        assert "### Support & Feedback" in footer_text
        
        # Check for metadata
        assert "**📅 Consolidated:**" in footer_text
        assert "**🔧 System:**" in footer_text
        assert "**📊 Format:**" in footer_text
        assert "**🔍 Structure:**" in footer_text
    
    def test_file_title_formatting(self, generator):
        """Test file title formatting functionality."""
        # Test basic formatting
        assert generator._format_file_title("payment_setup.md") == "Payment Setup"
        assert generator._format_file_title("TOURNAMENT_GUIDE.md") == "Tournament Guide"
        
        # Test task file formatting
        assert generator._format_file_title("TASK_5_1_COMPLETE.md") == "Task 5.1 Complete"
        assert generator._format_file_title("TASK_10_15_SUMMARY.md") == "Task 10.15 Summary"
        
        # Test special word handling
        assert generator._format_file_title("api_reference.md") == "API Reference"
        assert generator._format_file_title("http_and_json_guide.md") == "HTTP and JSON Guide"
    
    def test_file_description_creation(self, generator, sample_file_analyses):
        """Test file description creation."""
        # Test feature guide description
        feature_analysis = sample_file_analyses[0]  # PAYMENT_SETUP.md
        description = generator._create_file_description(feature_analysis)
        
        assert "🎯 Feature implementation guide" in description
        assert "(1,200 words)" in description
        assert "Topics: payment, setup, configuration" in description
        
        # Test completion summary description
        completion_analysis = sample_file_analyses[2]  # TASK_5_1_COMPLETE.md
        description = generator._create_file_description(completion_analysis)
        
        assert "📋 Implementation completion summary" in description
        assert "(800 words)" in description
    
    def test_file_type_determination(self, generator, sample_file_analyses):
        """Test file type determination for grouping."""
        # Test feature guide
        assert generator._determine_file_type(sample_file_analyses[0]) == "Feature Guides"
        
        # Test completion summary
        assert generator._determine_file_type(sample_file_analyses[2]) == "Implementation Records"
        
        # Test quick reference
        assert generator._determine_file_type(sample_file_analyses[3]) == "Quick References"
        
        # Test test report
        assert generator._determine_file_type(sample_file_analyses[4]) == "Test Reports"
    
    def test_category_icons(self, generator):
        """Test category icon assignment."""
        assert generator._get_category_icon(Category.SETUP_CONFIG) == "🛠️"
        assert generator._get_category_icon(Category.FEATURE_DOCS) == "🎯"
        assert generator._get_category_icon(Category.INTEGRATION_GUIDES) == "🔗"
        assert generator._get_category_icon(Category.TESTING_VALIDATION) == "🧪"
        assert generator._get_category_icon(Category.QUICK_REFERENCES) == "🔍"
        assert generator._get_category_icon(Category.IMPLEMENTATION_COMPLETION) == "📊"
        assert generator._get_category_icon(Category.HISTORICAL_ARCHIVE) == "📚"
    
    def test_enhanced_category_descriptions(self, generator):
        """Test enhanced category descriptions."""
        desc = generator._get_enhanced_category_description(Category.FEATURE_DOCS)
        assert "Comprehensive documentation for all system features" in desc
        
        desc = generator._get_enhanced_category_description(Category.TESTING_VALIDATION)
        assert "Testing frameworks, validation procedures" in desc
    
    def test_documentation_statistics_calculation(self, generator, sample_file_analyses, 
                                                 sample_consolidated_groups):
        """Test documentation statistics calculation."""
        stats = generator._calculate_documentation_statistics(
            sample_file_analyses, sample_consolidated_groups
        )
        
        # Check basic statistics
        assert stats['total_documents'] == 5
        assert stats['consolidated_groups'] == 2
        assert stats['total_words'] == 6600  # Sum of all word counts
        assert stats['categories_covered'] == 4  # Number of unique categories
        
        # Check category breakdown
        assert stats['category_breakdown'][Category.FEATURE_DOCS] == 2
        assert stats['category_breakdown'][Category.IMPLEMENTATION_COMPLETION] == 1
        assert stats['category_breakdown'][Category.QUICK_REFERENCES] == 1
        assert stats['category_breakdown'][Category.TESTING_VALIDATION] == 1
        
        # Check features covered
        assert 'Payment' in stats['features_covered']
        assert 'Tournament' in stats['features_covered']
        
        # Check calculated metrics
        assert stats['avg_document_length'] == 1320  # 6600 / 5
        assert stats['coverage_score'] >= 6  # Should be reasonable score
        assert stats['last_updated'] == '2024-01-25'  # Most recent date
    
    def test_update_frequency_calculation(self, generator):
        """Test update frequency calculation."""
        recent_files = [
            {'date': datetime(2024, 1, 25)},  # 0 days ago (if today is 2024-01-25)
            {'date': datetime(2024, 1, 20)},  # 5 days ago
            {'date': datetime(2024, 1, 15)},  # 10 days ago
            {'date': datetime(2023, 12, 1)},  # ~55 days ago
            {'date': datetime(2023, 10, 1)},  # ~116 days ago
        ]
        
        with patch('doc_consolidation.generator.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 25)
            stats = generator._calculate_update_frequency(recent_files)
        
        # Note: Exact counts depend on the mock date, but structure should be correct
        assert 'Last 7 days' in stats
        assert 'Last 30 days' in stats
        assert 'Last 90 days' in stats
        assert 'Older' in stats
        assert sum(stats.values()) == 5  # All files accounted for
    
    def test_master_index_requirements_compliance(self, generator, sample_structure, 
                                                 sample_file_analyses, sample_consolidated_groups):
        """Test that master index meets all task requirements."""
        index_content = generator.generate_master_index(
            sample_structure, sample_file_analyses, sample_consolidated_groups
        )
        
        # Requirement 4.1: Generate comprehensive README.md in docs/ directory
        assert "# Documentation Index" in index_content
        assert len(index_content) > 5000  # Comprehensive content
        
        # Requirement 4.2: Organize links by category with clear descriptions
        assert "## 📚 Documentation Catalog" in index_content
        assert "### By Category" in index_content
        assert "Feature-specific documentation" in index_content
        
        # Requirement 4.3: Include quick-start sections for developers
        assert "## 🚀 Quick Start Guide" in index_content
        assert "### New to the Project?" in index_content
        assert "### Experienced Developer?" in index_content
        assert "### Common Developer Tasks" in index_content
        
        # Requirement 4.4: Maintain consistent naming conventions
        assert "[Setup & Configuration](setup/)" in index_content
        assert "[Feature Documentation](features/)" in index_content
        assert "[Testing Guide](testing/)" in index_content
        
        # Requirement 4.5: Provide search-friendly organization
        assert "## 🔍 Navigation & Search Guide" in index_content
        assert "### Finding What You Need" in index_content
        assert "### Search Strategies" in index_content


class TestEnhancedCategoryIndexGeneration:
    """Test enhanced category index generation functionality."""
    
    @pytest.fixture
    def generator(self):
        """Create a StructureGenerator instance for testing."""
        config = ConsolidationConfig()
        return StructureGenerator(config)
    
    @pytest.fixture
    def sample_structure(self):
        """Create a sample DocumentationStructure for testing."""
        return DocumentationStructure()
    
    @pytest.fixture
    def sample_organized_files(self):
        """Create sample organized files mapping."""
        return {
            'PAYMENT_SETUP.md': 'docs/features/payments/payment_setup.md',
            'TOURNAMENT_GUIDE.md': 'docs/features/tournaments/tournament_guide.md',
            'AUTH_CONFIG.md': 'docs/features/authentication/auth_config.md',
            'TASK_5_1_COMPLETE.md': 'docs/implementation/completion-summaries/task_5_1_complete.md',
            'QUICK_SETUP.md': 'docs/reference/quick_setup.md',
            'test_results.md': 'docs/testing/test-reports/test_results.md'
        }
    
    def test_create_enhanced_category_indexes(self, generator, sample_structure, sample_organized_files):
        """Test creation of enhanced category indexes."""
        with patch('builtins.open', create=True) as mock_open:
            mock_file = Mock()
            mock_open.return_value.__enter__.return_value = mock_file
            
            category_indexes = generator.create_category_indexes(sample_structure, sample_organized_files)
            
            # Check that indexes were created for all categories
            expected_categories = ['setup', 'features', 'development', 'testing', 'reference', 'implementation', 'archive']
            for category in expected_categories:
                assert category in category_indexes
            
            # Check that files were written
            assert mock_open.call_count == len(expected_categories)
    
    def test_enhanced_category_index_structure(self, generator, sample_structure, sample_organized_files):
        """Test structure of enhanced category index."""
        category = Category.FEATURE_DOCS
        config = sample_structure.categories[category]
        
        index_content = generator._generate_enhanced_category_index(
            category, config, sample_organized_files
        )
        
        # Check enhanced structure
        assert "# 🎯 Features" in index_content
        assert "## 🚀 Quick Navigation" in index_content
        assert "## 📋 Available Documentation" in index_content
        assert "## 📁 Subdirectories" in index_content
        assert "## 🔗 Related Resources" in index_content
        
        # Check for table format in quick navigation
        assert "| Resource | Description |" in index_content
        assert "|----------|-------------|" in index_content
        
        # Check for enhanced footer
        assert "📚 **[← Back to Main Documentation Index](../README.md)**" in index_content
        assert f"*Last updated: {datetime.now().strftime('%Y-%m-%d')}*" in index_content
    
    def test_category_quick_links(self, generator):
        """Test category-specific quick links generation."""
        # Test setup category links
        links = generator._get_category_quick_links(Category.SETUP_CONFIG, Mock())
        link_texts = [link[0] for link in links]
        assert "🛠️ Installation Guide" in link_texts
        assert "⚙️ Configuration" in link_texts
        assert "🔧 Troubleshooting" in link_texts
        
        # Test feature category links
        links = generator._get_category_quick_links(Category.FEATURE_DOCS, Mock())
        link_texts = [link[0] for link in links]
        assert "💳 Payment System" in link_texts
        assert "🏆 Tournament System" in link_texts
        assert "🔐 Authentication" in link_texts
    
    def test_organized_category_files_extraction(self, generator, sample_organized_files):
        """Test extraction of organized files for a category."""
        files = generator._get_organized_category_files('features', sample_organized_files)
        
        # Should find files in features directory
        filenames = [f['filename'] for f in files]
        assert 'payment_setup.md' in filenames
        assert 'tournament_guide.md' in filenames
        assert 'auth_config.md' in filenames
        
        # Should not find files from other categories
        assert 'task_5_1_complete.md' not in filenames
        assert 'quick_setup.md' not in filenames
    
    def test_files_grouping_by_subdirectory(self, generator, sample_structure):
        """Test grouping of files by subdirectory."""
        files = [
            {'filename': 'main_guide.md', 'subdir': ''},
            {'filename': 'payment_setup.md', 'subdir': 'payments'},
            {'filename': 'tournament_guide.md', 'subdir': 'tournaments'},
            {'filename': 'payment_api.md', 'subdir': 'payments'},
        ]
        
        config = sample_structure.categories[Category.FEATURE_DOCS]
        grouped = generator._group_files_by_subdirectory(files, config)
        
        # Check grouping
        assert '' in grouped  # Main directory
        assert 'payments' in grouped
        assert 'tournaments' in grouped
        
        assert len(grouped['']) == 1
        assert len(grouped['payments']) == 2
        assert len(grouped['tournaments']) == 1
    
    def test_subdirectory_descriptions(self, generator):
        """Test subdirectory description generation."""
        assert "User authentication and authorization" in generator._get_subdirectory_description(
            Category.FEATURE_DOCS, 'authentication'
        )
        assert "Payment processing and financial" in generator._get_subdirectory_description(
            Category.FEATURE_DOCS, 'payments'
        )
        assert "Tournament management and competition" in generator._get_subdirectory_description(
            Category.FEATURE_DOCS, 'tournaments'
        )
        assert "Automated test execution results" in generator._get_subdirectory_description(
            Category.TESTING_VALIDATION, 'test-reports'
        )
    
    def test_category_help_sections(self, generator):
        """Test category-specific help section generation."""
        # Test setup category help
        help_section = generator._generate_category_help_section(Category.SETUP_CONFIG)
        help_text = "\n".join(help_section)
        
        assert "## 🆘 Getting Help with Setup" in help_text
        assert "**Common Setup Issues:**" in help_text
        assert "**Still Need Help?**" in help_text
        
        # Test feature category help
        help_section = generator._generate_category_help_section(Category.FEATURE_DOCS)
        help_text = "\n".join(help_section)
        
        assert "## 🎯 Feature Documentation Guide" in help_text
        assert "**Understanding Features:**" in help_text
        assert "**Implementation Status:**" in help_text
        
        # Test testing category help
        help_section = generator._generate_category_help_section(Category.TESTING_VALIDATION)
        help_text = "\n".join(help_section)
        
        assert "## 🧪 Testing Guide" in help_text
        assert "**Running Tests:**" in help_text
        assert "**Writing Tests:**" in help_text


if __name__ == '__main__':
    pytest.main([__file__, '-v'])