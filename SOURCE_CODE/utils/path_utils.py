# SOURCE_CODE/utils/path_utils.py
import os
from pathlib import Path
from typing import Optional, Union

class PathManager:
    """Centralized path management for the application"""
    
    def __init__(self, project_root: Optional[Path] = None):
        if project_root is None:
            # Auto-detect project root (go up from SOURCE_CODE/utils)
            self.project_root = Path(__file__).resolve().parent.parent.parent
        else:
            self.project_root = Path(project_root)
        
        # Source code directory
        self.src_dir = self.project_root / "SOURCE_CODE"
        
        # Source code subdirectories
        self.utils_dir = self.src_dir / "utils"
        self.pipelines_dir = self.src_dir / "pipelines"
        self.ui_dir = self.src_dir / "ui"
        self.sr_dir = self.pipelines_dir / "sr"
        self.doc_dir = self.src_dir / "docs"  # AI reference docs
        
        # Prompts
        self.prompts_dir = self.project_root / "prompts"
        
        # User documentation (with mode subfolders)
        self.docs_dir = self.project_root / "docs"
        
        # Reader documentation ([Readme] folder)
        self.readme_dir = self.project_root / "Readme"
        
        # Assets
        self.assets_dir = self.project_root / "assets"
        
        # Scripts
        self.scripts_dir = self.project_root / "scripts"
        self.scripts_windows_dir = self.scripts_dir / "windows"
        self.scripts_macos_dir = self.scripts_dir / "macos"
        
        # Docker
        self.docker_dir = self.project_root / "docker"
        
        # Data directories
        self.input_dir = self.project_root / "input"
        self.output_dir = self.project_root / "output"
        self.reports_dir = self.project_root / "reports"
        self.data_dir = self.project_root / "data"
        self.chroma_db_dir = self.project_root / "chroma_db"
        
        # Tests
        self.tests_dir = self.project_root / "tests"
        
        # Ensure all directories exist
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure all required directories exist"""
        # Main directories
        main_dirs = [
            self.src_dir, self.utils_dir, self.pipelines_dir,
            self.ui_dir, self.sr_dir, self.doc_dir,
            self.prompts_dir, self.docs_dir, self.readme_dir,
            self.assets_dir, self.scripts_dir,
            self.scripts_windows_dir, self.scripts_macos_dir,
            self.docker_dir, self.input_dir, self.output_dir,
            self.reports_dir, self.data_dir, self.chroma_db_dir,
            self.tests_dir
        ]
        
        for d in main_dirs:
            d.mkdir(parents=True, exist_ok=True)
        
        # Create mode subdirectories
        mode_subdirs = ['coding', 'writing', 'appraisal', 'search', 'rct_search', 'sr']
        for mode in mode_subdirs:
            # docs/ subdirectories
            (self.docs_dir / mode).mkdir(parents=True, exist_ok=True)
            
            # input/ subdirectories
            (self.input_dir / mode).mkdir(parents=True, exist_ok=True)
            
            # output/ subdirectories
            (self.output_dir / mode).mkdir(parents=True, exist_ok=True)
            
            # reports/ subdirectories
            (self.reports_dir / mode).mkdir(parents=True, exist_ok=True)
    
    # Input/Output path getters
    def get_input_path(self, mode: str) -> Path:
        """Get input path for a specific mode"""
        return self.input_dir / mode
    
    def get_output_path(self, mode: str) -> Path:
        """Get output path for a specific mode"""
        return self.output_dir / mode
    
    def get_reports_path(self, mode: str) -> Path:
        """Get reports path for a specific mode"""
        return self.reports_dir / mode
    
    def get_rag_db_path(self, mode: str) -> Path:
        """Get RAG database path for a specific mode"""
        return self.chroma_db_dir / f"{mode}_rag_db"
    
    def get_docs_mode_path(self, mode: str) -> Path:
        """Get docs path for a specific mode"""
        return self.docs_dir / mode
    
    def get_mode_reference_path(self, mode: str) -> Path:
        """Get AI reference doc path for a specific mode"""
        return self.doc_dir / "modes" / f"{mode}.md"
    
    def get_prompt_path(self, prompt_name: str) -> Path:
        """Get prompt file path"""
        return self.prompts_dir / f"{prompt_name}-prompt.md"
    
    # Utility methods
    def get_project_root(self) -> Path:
        return self.project_root
    
    def get_assets_path(self, asset_name: str) -> Path:
        return self.assets_dir / asset_name
    
    def get_readme_path(self, doc_name: str) -> Path:
        return self.readme_dir / doc_name
    
    def get_docker_path(self, file_name: str) -> Path:
        return self.docker_dir / file_name

# Create a global instance
PATH_MANAGER = PathManager()

# Convenience functions for easy imports
def get_project_root() -> Path:
    return PATH_MANAGER.project_root

def get_src_dir() -> Path:
    return PATH_MANAGER.src_dir

def get_input_dir(mode: Optional[str] = None) -> Path:
    if mode:
        return PATH_MANAGER.get_input_path(mode)
    return PATH_MANAGER.input_dir

def get_output_dir(mode: Optional[str] = None) -> Path:
    if mode:
        return PATH_MANAGER.get_output_path(mode)
    return PATH_MANAGER.output_dir

def get_reports_dir(mode: Optional[str] = None) -> Path:
    if mode:
        return PATH_MANAGER.get_reports_path(mode)
    return PATH_MANAGER.reports_dir

def get_rag_db(mode: str) -> Path:
    return PATH_MANAGER.get_rag_db_path(mode)

def get_docs_mode(mode: str) -> Path:
    return PATH_MANAGER.get_docs_mode_path(mode)

def get_mode_reference(mode: str) -> Path:
    return PATH_MANAGER.get_mode_reference_path(mode)

def get_prompt(prompt_name: str) -> Path:
    return PATH_MANAGER.get_prompt_path(prompt_name)

def get_assets(asset_name: str) -> Path:
    return PATH_MANAGER.get_assets_path(asset_name)

def get_readme(doc_name: str) -> Path:
    return PATH_MANAGER.get_readme_path(doc_name)

def get_docker_file(file_name: str) -> Path:
    return PATH_MANAGER.get_docker_path(file_name)