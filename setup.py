from setuptools import find_packages, setup


setup(
    name='inventree-repairpro-brother-ql-relay',
    version='0.1.3',
    description='InvenTree 0.17.14 machine driver for the RepairPro Brother QL-700 relay',
    packages=find_packages(),
    include_package_data=True,
    python_requires='>=3.9',
    install_requires=['requests>=2.32,<3'],
    entry_points={
        'inventree_plugins': [
            'RepairProBrotherQlPlugin = inventree_repairpro_brother.plugin:RepairProBrotherQlPlugin',
        ],
    },
)
