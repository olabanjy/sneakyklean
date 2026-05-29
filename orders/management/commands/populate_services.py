"""
Management command to populate initial services
"""
from django.core.management.base import BaseCommand
from orders.models import Service
from decimal import Decimal


class Command(BaseCommand):
    help = 'Populate initial cleaning services with prices'
    
    def handle(self, *args, **options):
        services_data = [
            {
                'name': 'Basic Cleaning',
                'description': 'Standard cleaning for everyday sneakers. Includes surface cleaning, deodorizing, and basic stain removal.',
                'price': Decimal('7000'),
                'display_order': 1,
                'icon': 'mdi-shoe-sneaker',
                'estimated_duration': '1-2 hours'
            },
            {
                'name': 'Deep Cleaning',
                'description': 'Thorough deep clean for heavily soiled sneakers. Includes premium cleaning agents,  machine washing, and deep stain removal.',
                'price': Decimal('12000'),
                'display_order': 2,
                'icon': 'mdi-spray-bottle',
                'estimated_duration': '2-3 hours'
            },
            {
                'name': 'Restoration',
                'description': 'Complete restoration for damaged or aged sneakers. Includes color restoration, sole cleaning, and minor repairs.',
                'price': Decimal('25000'),
                'display_order': 3,
                'icon': 'mdi-auto-fix',
                'estimated_duration': '4-6 hours'
            },
            {
                'name': 'Suede Care',
                'description': 'Specialized care for suede and nubuck materials. Includes gentle cleaning, brushing, and protective treatment.',
                'price': Decimal('15000'),
                'display_order': 4,
                'icon': 'mdi-brush',
                'estimated_duration': '2-3 hours'
            }
        ]
        
        created_count = 0
        updated_count = 0
        
        for service_data in services_data:
            service, created = Service.objects.update_or_create(
                name=service_data['name'],
                defaults={
                    'description': service_data['description'],
                    'price': service_data['price'],
                    'display_order': service_data['display_order'],
                    'icon': service_data['icon'],
                    'estimated_duration': service_data['estimated_duration'],
                    'is_active': True
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created: {service.name} - ₦{service.price:,.0f}')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'↻ Updated: {service.name} - ₦{service.price:,.0f}')
                )
        
        self.stdout.write(self.style.SUCCESS(f'\nSummary: {created_count} created, {updated_count} updated'))
        self.stdout.write(self.style.SUCCESS(f'Total services in database: {Service.objects.count()}'))
