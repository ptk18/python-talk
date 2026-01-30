class PetShelter:
    def register_animal(self, name, species, age):
        """Register a new animal arriving at the shelter."""
        return f"Registered {species} named '{name}', age {age}"

    def adopt_animal(self, animal_name, adopter_name):
        """Process the adoption of an animal to a new owner."""
        return f"'{animal_name}' adopted by {adopter_name}"

    def schedule_vaccination(self, animal_name, vaccine_type):
        """Schedule a vaccination appointment for an animal."""
        return f"Scheduled {vaccine_type} vaccination for '{animal_name}'"

    def mark_as_neutered(self, animal_name):
        """Record that an animal has been spayed or neutered."""
        return f"'{animal_name}' marked as neutered"

    def is_available_for_adoption(self, animal_name):
        """Check if an animal is currently available for adoption."""
        return True

    def list_animals_by_species(self, species):
        """Return all animals of a given species currently in the shelter."""
        return [f"Buddy the {species}", f"Max the {species}", f"Luna the {species}"]

    def record_medical_checkup(self, animal_name, notes):
        """Record the results of a medical examination."""
        return f"Medical checkup recorded for '{animal_name}': {notes}"

    def transfer_to_foster(self, animal_name, foster_parent):
        """Transfer an animal to a foster home."""
        return f"'{animal_name}' transferred to foster parent {foster_parent}"
